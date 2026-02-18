"""
Download API Routes
Handles anime information fetching, download job management, and execution
"""
from flask import Blueprint, jsonify, request, current_app
import threading
import os
from datetime import datetime
import logging
from app.utils import login_required
from app.downloader import AnimeDownloader
from app.models import DownloadJob
from app.extensions import socketio
from app.download_eta_calculator import AdvancedETACalculator, format_speed
from app.plugin_manager import PluginManager
from app.job_store import JobStore

download_bp = Blueprint('download', __name__, url_prefix='/api/download')

logger = logging.getLogger(__name__)


def _build_job_store() -> JobStore:
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'downloads', 'jobs.sqlite3')
    return JobStore(os.path.abspath(db_path))


job_store = _build_job_store()


def _persist_job(job: DownloadJob) -> None:
    try:
        job_store.upsert_job(job.job_id, job.anime_url, job.config, job.to_dict())
    except Exception as e:
        logger.warning("Failed to persist job %s: %s", job.job_id, e)


def _hydrate_jobs_from_store() -> None:
    global job_counter
    try:
        rows = job_store.load_jobs()
        for row in rows:
            job = DownloadJob(row["job_id"], row["anime_url"], row["config"])
            state = row.get("state", {})
            for key, value in state.items():
                if key in {"start_time", "end_time"} and value:
                    try:
                        setattr(job, key, datetime.fromisoformat(value))
                    except Exception:
                        continue
                elif hasattr(job, key):
                    setattr(job, key, value)
            download_jobs[job.job_id] = job
        job_counter = max(job_counter, job_store.get_max_job_id())
    except Exception as e:
        logger.warning("Failed loading jobs from store: %s", e)


# Global storage for download jobs
download_jobs = {}
job_counter = 0
job_lock = threading.Lock()

job_emitters = {}
job_emitters_lock = threading.Lock()
plugin_manager = PluginManager()


def _categorize_failure(job: DownloadJob) -> str:
    err = (job.error or "").lower()
    recent_logs = "\n".join((l.get("message") or "") for l in (job.logs or [])[-20:]).lower()
    blob = f"{err}\n{recent_logs}"

    if any(k in blob for k in ["timeout", "timed out", "connection", "network", "403", "429"]):
        return "network_or_rate_limit"
    if any(k in blob for k in ["merge", "concat", "ffmpeg"]):
        return "merge_failure"
    if any(k in blob for k in ["no servers", "could not choose server", "resolve video data", "episode token"]):
        return "source_resolution_failure"
    if any(k in blob for k in ["plugin", "extractor", "unsupported", "youtube"]):
        return "plugin_failure"
    return "unknown"


def _build_recovery_plan(job: DownloadJob) -> list:
    category = _categorize_failure(job)
    config = dict(job.config or {})
    plan = []

    if category == "merge_failure" and config.get("merge_episodes"):
        plan.append({
            "label": "Retry without merging",
            "changes": {"merge_episodes": False, "keep_individual_files": True},
        })

    if category in {"source_resolution_failure", "network_or_rate_limit", "unknown"}:
        plan.append({
            "label": "Switch server preference",
            "changes": {
                "prefer_server": "Server 2" if str(config.get("prefer_server", "Server 1")).lower() == "server 1" else "Server 1"
            },
        })
        plan.append({
            "label": "Lower quality and FPS",
            "changes": {"quality": "720", "fps": "30"},
        })

    if category in {"plugin_failure", "unknown"}:
        plan.append({
            "label": "Toggle plugin engine",
            "changes": {"use_plugin": not bool(config.get("use_plugin", True))},
        })

    if category == "network_or_rate_limit":
        plan.append({
            "label": "Increase timeout and retries",
            "changes": {
                "timeout": max(450, int(config.get("timeout", 300))),
                "max_retries": max(9, int(config.get("max_retries", 7))),
            },
        })

    if not plan:
        plan.append({"label": "Retry with same settings", "changes": {}})

    return plan


def _create_job(anime_url: str, config: dict, *, parent_job_id=None, retry_count=0, recovery_plan=None) -> DownloadJob:
    global job_counter
    with job_lock:
        job_counter += 1
        job_id = job_counter
    job = DownloadJob(job_id, anime_url, config)
    job.parent_job_id = parent_job_id
    job.retry_count = retry_count
    job.recovery_plan = recovery_plan or []
    download_jobs[job_id] = job
    _persist_job(job)
    return job


def _extract_number(value):
    try:
        digits = "".join(c for c in str(value) if c.isdigit())
        return int(digits) if digits else None
    except Exception:
        return None


def _collect_stream_options(downloader: AnimeDownloader, episode: dict):
    type_labels = {"sub": "Hard Sub", "softsub": "Soft Sub", "dub": "Dub (with subs)"}
    options = {
        "available_types": [],
        "available_servers": [],
        "available_qualities": ["best"],
        "available_fps": ["best"],
    }
    try:
        servers = downloader.get_video_servers(episode.get("token", ""))
        if not servers:
            return options

        by_type = {}
        for server in servers:
            stype = server.get("type") or ""
            by_type.setdefault(stype, []).append(server)
            sname = server.get("server_name")
            if sname and sname not in options["available_servers"]:
                options["available_servers"].append(sname)

        for stype, _items in by_type.items():
            label = type_labels.get(stype)
            if label and label not in options["available_types"]:
                options["available_types"].append(label)

        candidate = servers[0]
        soft = by_type.get("softsub")
        if soft:
            candidate = soft[0]

        video_data = downloader.get_video_data(candidate.get("server_id", ""))
        qualities = set()
        for source in (video_data or {}).get("sources", []):
            q = source.get("quality")
            if not q:
                continue
            q_num = _extract_number(q)
            qualities.add((q_num or 10**9, str(q)))

        if qualities:
            options["available_qualities"] = ["best"] + [q for _n, q in sorted(qualities)]
    except Exception as e:
        logger.debug("Failed summing completed file sizes for job %s: %s", job.job_id, e)

    return options


def _sum_downloaded_bytes(job: DownloadJob, download_folder: str) -> int:
    total = 0
    try:
        if job.anime_title:
            job_dir = os.path.join(download_folder, job.anime_title)
            for name in job.downloaded_files or []:
                p = os.path.join(job_dir, name)
                if os.path.exists(p) and os.path.isfile(p):
                    total += os.path.getsize(p)
    except Exception as e:
        logger.debug("Failed summing current file size for job %s: %s", job.job_id, e)

    try:
        if job.anime_title and job.current_file:
            p = os.path.join(download_folder, job.anime_title, job.current_file)
            if os.path.exists(p) and os.path.isfile(p):
                total += os.path.getsize(p)
    except Exception as e:
        logger.debug("Non-fatal stream option collection error: %s", e)
    return total


def _start_job_emitter(job: DownloadJob, download_folder: str) -> None:
    with job_emitters_lock:
        if job.job_id in job_emitters:
            return

    def _run() -> None:
        calc = AdvancedETACalculator(window_size=8)
        last_bytes = 0
        calc_started = False

        while job.status not in {"completed", "failed"}:
            try:
                if (not calc_started) and job.total_episodes and job.total_episodes > 0:
                    calc.start(float(job.total_episodes))
                    calc_started = True

                downloaded_units = float(job.completed_episodes)
                eta_info = calc.update(downloaded_units) if calc_started else None

                downloaded_bytes = _sum_downloaded_bytes(job, download_folder)
                job.downloaded_bytes = downloaded_bytes

                delta = max(0, downloaded_bytes - last_bytes)
                last_bytes = downloaded_bytes

                job.speed_bps = float(delta)
                job.speed_formatted = format_speed(float(delta))
                if eta_info:
                    job.eta_seconds = eta_info.get("eta_seconds")
                    job.eta_formatted = eta_info.get("eta_formatted")
                else:
                    job.eta_seconds = None
                    job.eta_formatted = None

                _persist_job(job)

                socketio.emit("job_update", job.to_dict())
                socketio.emit(
                    "progress_update",
                    {
                        "job_id": job.job_id,
                        "progress": job.progress,
                        "speed": job.speed_formatted or "0 B/s",
                        "eta": job.eta_formatted or "Calculating...",
                    },
                )
            except Exception as e:
                logger.debug("Emitter update failed for job %s: %s", job.job_id, e)
            finally:
                try:
                    threading.Event().wait(1.0)
                except Exception as e:
                    logger.debug("Emitter sleep failed for job %s: %s", job.job_id, e)

        try:
            socketio.emit("job_update", job.to_dict())
        except Exception as e:
            logger.debug("Final emitter push failed for job %s: %s", job.job_id, e)

        with job_emitters_lock:
            job_emitters.pop(job.job_id, None)

    t = threading.Thread(target=_run, daemon=True)
    with job_emitters_lock:
        job_emitters[job.job_id] = t
    t.start()

def run_download_job(job: DownloadJob, download_folder):
    """Execute the download job in a separate thread"""
    try:
        plugin_enabled = bool(job.config.get("use_plugin", True))

        if plugin_enabled:
            plugin = plugin_manager.get_plugin_for_url(job.anime_url)
            if getattr(plugin, "SITE_NAME", "") != "AniKai.to":
                job.status = "downloading"
                job.add_log("INFO", f"Using plugin backend: {getattr(plugin, 'SITE_NAME', plugin.__class__.__name__)}")
                generic_out = os.path.join(download_folder, "plugin_downloads")
                result = plugin_manager.download(
                    job.anime_url,
                    generic_out,
                    quality=job.config.get("quality"),
                    fps=job.config.get("fps"),
                    prefer_type=job.config.get("prefer_type", "Soft Sub"),
                    prefer_server=job.config.get("prefer_server", "Server 1"),
                )
                if not result.get("success"):
                    raise Exception(result.get("error") or "Plugin download failed")

                files = result.get("files", [])
                job.total_episodes = len(files) or 1
                job.completed_episodes = len(files) or 1
                job.progress = 100
                job.downloaded_files = [os.path.basename(p) for p in files]
                meta = result.get("metadata", {}) or {}
                job.anime_title = meta.get("title") or "Plugin Download"
                job.status = "completed"
                job.end_time = datetime.now()
                job.add_log("INFO", f"🎉 Plugin download completed ({len(files)} file(s))")
                _persist_job(job)
                return

        # Initialize downloader
        downloader = AnimeDownloader(config={
            "download_method": job.config.get("download_method", "yt-dlp"),
            "max_retries": job.config.get("max_retries", 7),
            "timeout": job.config.get("timeout", 300),
            "max_workers": job.config.get("max_workers", 15),
        })

        # Set up callbacks
        def log_callback(level, msg):
            job.add_log(level, msg)

        downloader.set_log_callback(log_callback)

        # Get anime details
        job.status = "fetching_info"
        job.add_log("INFO", f"Fetching anime details from {job.anime_url}")
        
        anime_id, anime_title = downloader.get_anime_details(job.anime_url)
        if not anime_id:
            raise Exception("Could not extract anime ID from URL")

        job.anime_title = anime_title
        job.add_log("INFO", f"Found anime: {anime_title}")

        # Detect season
        detected_season = downloader.detect_season_from_title(anime_title)
        job.season = job.config.get("season_number", 0)
        if job.season == 0:
            job.season = detected_season
        job.add_log("INFO", f"Season: {job.season}")

        # Get episodes
        job.status = "fetching_episodes"
        episodes = downloader.get_episode_list(anime_id)
        if not episodes:
            raise Exception("No episodes found")

        job.add_log("INFO", f"Found {len(episodes)} episodes")

        # Filter episodes based on selection mode
        download_mode = job.config.get("download_mode", "All Episodes")
        if download_mode == "Single Episode":
            single_ep = job.config.get("single_episode", "1")
            selected = [ep for ep in episodes if ep["id"] == single_ep]
        elif download_mode == "Episode Range":
            start_ep = job.config.get("start_episode", "1")
            end_ep = job.config.get("end_episode", "1")
            
            def in_range(ep_id, start_id, end_id):
                start_key = downloader.safe_episode_key(start_id)
                end_key = downloader.safe_episode_key(end_id)
                key = downloader.safe_episode_key(ep_id)
                return start_key <= key <= end_key
            
            selected = [ep for ep in episodes if in_range(ep["id"], start_ep, end_ep)]
        else:  # All Episodes
            selected = episodes

        if not selected:
            raise Exception("No episodes match your selection")

        job.total_episodes = len(selected)
        job.add_log("INFO", f"Will download {job.total_episodes} episode(s)")

        # Create download directory
        download_dir = os.path.join(download_folder, anime_title)
        os.makedirs(download_dir, exist_ok=True)

        # Download episodes
        job.status = "downloading"
        downloaded_files = []
        prefer_type = job.config.get("prefer_type", "Soft Sub")
        prefer_server = job.config.get("prefer_server", "Server 1")

        for idx, ep in enumerate(selected, 1):
            ep_id = ep["id"]
            job.current_episode = ep_id
            job.add_log("INFO", f"Processing episode {ep_id} ({idx}/{job.total_episodes})")

            # Get servers
            servers = downloader.get_video_servers(ep["token"])
            if not servers:
                job.add_log("ERROR", f"No servers available for episode {ep_id}")
                continue

            # Choose server
            server = downloader.choose_server(servers, prefer_type, prefer_server)
            if not server:
                job.add_log("ERROR", f"Could not choose server for episode {ep_id}")
                continue

            job.add_log("INFO", f"Using server: {server['server_name']}")

            # Get video data
            video_data = downloader.get_video_data(server["server_id"])
            if not video_data:
                job.add_log("ERROR", f"Could not resolve video data for episode {ep_id}")
                continue

            # Generate filename
            filename = downloader.generate_episode_filename(anime_title, job.season, ep_id)
            filepath = os.path.join(download_dir, filename)
            job.current_file = os.path.basename(filepath)

            # Download episode
            if downloader.download_episode(
                video_data,
                filepath,
                ep_id,
                quality=job.config.get("quality"),
                fps=job.config.get("fps"),
            ):
                downloaded_files.append(filepath)
                job.completed_episodes += 1
                job.progress = int((job.completed_episodes / job.total_episodes) * 100)
                job.downloaded_files.append(os.path.basename(filepath))
                job.current_file = None
                job.add_log("INFO", f"✅ Successfully downloaded episode {ep_id}")
                _persist_job(job)
            else:
                job.current_file = None
                job.add_log("ERROR", f"❌ Failed to download episode {ep_id}")
                _persist_job(job)

        # Merge if requested and multiple episodes
        merge_episodes = job.config.get("merge_episodes", False)
        if merge_episodes and len(downloaded_files) > 1:
            job.status = "merging"
            job.add_log("INFO", f"Merging {len(downloaded_files)} episodes...")
            
            first_ep_id = selected[0]["id"]
            last_ep_id = selected[-1]["id"]
            
            merged_file = downloader.merge_videos(
                downloaded_files,
                anime_title,
                job.season,
                first_ep_id,
                last_ep_id
            )

            if merged_file:
                job.merged_file = os.path.basename(merged_file)
                job.add_log("INFO", f"✅ Successfully merged into {job.merged_file}")
                
                # Remove individual files if requested
                if not job.config.get("keep_individual_files", False):
                    job.add_log("INFO", "Removing individual episode files...")
                    for f in downloaded_files:
                        try:
                            os.remove(f)
                            job.downloaded_files.remove(os.path.basename(f))
                        except Exception as e:
                            job.add_log("WARN", f"Could not remove {os.path.basename(f)}: {e}")
            else:
                job.add_log("ERROR", "❌ Merge failed")

        # Complete
        job.status = "completed"
        job.progress = 100
        job.current_file = None
        job.end_time = datetime.now()
        job.add_log("INFO", f"🎉 Download job completed! Downloaded {job.completed_episodes}/{job.total_episodes} episodes")
        _persist_job(job)

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.failure_reason = str(e)
        job.failure_category = _categorize_failure(job)
        job.recovery_plan = _build_recovery_plan(job)
        job.current_file = None
        job.end_time = datetime.now()
        job.add_log("ERROR", f"Job failed: {e}")
        import traceback
        job.add_log("ERROR", traceback.format_exc())
        _persist_job(job)

@download_bp.route('/anime/info', methods=['POST'])
@login_required
def get_anime_info():
    """Get anime information from URL"""
    try:
        data = request.json
        anime_url = data.get('anime_url')
        
        if not anime_url:
            return jsonify({"error": "No URL provided"}), 400

        downloader = AnimeDownloader()
        anime_id, anime_title = downloader.get_anime_details(anime_url)
        
        if not anime_id:
            return jsonify({"error": "Could not fetch anime information"}), 400

        episodes = downloader.get_episode_list(anime_id)
        season = downloader.detect_season_from_title(anime_title)
        stream_options = _collect_stream_options(downloader, episodes[0] if episodes else {})

        return jsonify({
            "anime_id": anime_id,
            "title": anime_title,
            "season": season,
            "total_episodes": len(episodes),
            "episodes": [{"id": ep["id"], "title": ep["title"]} for ep in episodes],
            **stream_options,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@download_bp.route('/start', methods=['POST'])
@login_required
def start_download():
    """Start a new download job"""
    global job_counter
    
    try:
        data = request.json
        anime_url = data.get('anime_url')
        
        if not anime_url:
            return jsonify({"error": "No URL provided"}), 400

        config = {
            "download_mode": data.get("download_mode", "All Episodes"),
            "single_episode": data.get("single_episode", "1"),
            "start_episode": data.get("start_episode", "1"),
            "end_episode": data.get("end_episode", "1"),
            "prefer_type": data.get("prefer_type", "Soft Sub"),
            "prefer_server": data.get("prefer_server", "Server 1"),
            "download_method": data.get("download_method", "yt-dlp"),
            "max_retries": data.get("max_retries", 7),
            "timeout": data.get("timeout", 300),
            "max_workers": data.get("max_workers", 15),
            "merge_episodes": data.get("merge_episodes", False),
            "season_number": data.get("season_number", 0),
            "keep_individual_files": data.get("keep_individual_files", False),
            "quality": data.get("quality", "best"),
            "fps": data.get("fps", "best"),
            "use_plugin": data.get("use_plugin", True),
        }

        job = _create_job(anime_url, config)

        _start_job_emitter(job, current_app.config['DOWNLOAD_FOLDER'])

        # Start download in background thread
        thread = threading.Thread(
            target=run_download_job, 
            args=(job, current_app.config['DOWNLOAD_FOLDER'])
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "job_id": job.job_id,
            "message": "Download job started"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@download_bp.route('/status/<int:job_id>', methods=['GET'])
@login_required
def get_download_status(job_id):
    """Get status of a download job"""
    job = download_jobs.get(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job.to_dict())

@download_bp.route('/list', methods=['GET'])
@login_required
def list_downloads():
    """List all download jobs"""
    jobs = [job.to_dict() for job in download_jobs.values()]
    # Sort by start time, newest first
    jobs.sort(key=lambda x: x['start_time'], reverse=True)
    return jsonify(jobs)

@download_bp.route('/clear/<int:job_id>', methods=['DELETE'])
@login_required
def clear_download_job(job_id):
    """Clear a completed/failed job from history"""
    if job_id in download_jobs:
        job = download_jobs[job_id]
        if job.status in ["completed", "failed"]:
            del download_jobs[job_id]
            job_store.delete_job(job_id)
            return jsonify({"message": "Job cleared"})
        else:
            return jsonify({"error": "Cannot clear active job"}), 400
    return jsonify({"error": "Job not found"}), 404


@download_bp.route('/plugins', methods=['GET'])
@login_required
def list_plugins():
    """List active downloader plugins"""
    return jsonify({"plugins": plugin_manager.list_plugins()})


@download_bp.route('/retry/<int:job_id>', methods=['POST'])
@login_required
def retry_download_job(job_id):
    """Create a new job using Download Doctor recovery suggestions."""
    old_job = download_jobs.get(job_id)
    if not old_job:
        return jsonify({"error": "Job not found"}), 404
    if old_job.status != "failed":
        return jsonify({"error": "Only failed jobs can be retried"}), 400

    data = request.json if isinstance(request.json, dict) else {}
    raw_action_index = data.get("action_index", 0)
    try:
        action_index = int(raw_action_index)
    except (TypeError, ValueError):
        return jsonify({"error": "action_index must be an integer"}), 400

    plan = old_job.recovery_plan or _build_recovery_plan(old_job)
    if not plan:
        plan = [{"label": "Retry with same settings", "changes": {}}]

    if action_index < 0 or action_index >= len(plan):
        return jsonify({"error": "Invalid action index"}), 400

    chosen = plan[action_index]
    new_config = dict(old_job.config or {})
    new_config.update(chosen.get("changes", {}))

    new_job = _create_job(
        old_job.anime_url,
        new_config,
        parent_job_id=old_job.job_id,
        retry_count=int(old_job.retry_count or 0) + 1,
        recovery_plan=plan,
    )
    new_job.add_log("INFO", f"🔁 Retry created from job #{old_job.job_id} using: {chosen.get('label', 'Recovery action')}")
    _persist_job(new_job)

    _start_job_emitter(new_job, current_app.config['DOWNLOAD_FOLDER'])
    thread = threading.Thread(target=run_download_job, args=(new_job, current_app.config['DOWNLOAD_FOLDER']))
    thread.daemon = True
    thread.start()

    return jsonify({
        "job_id": new_job.job_id,
        "parent_job_id": old_job.job_id,
        "selected_action": chosen,
        "message": "Retry job started",
    })


_hydrate_jobs_from_store()
