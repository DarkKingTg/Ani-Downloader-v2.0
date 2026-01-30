# Ani-Downloader Update Guide

## How to Update Ani-Downloader from GitHub

This guide explains how to safely update your Ani-Downloader installation when new versions are released on GitHub.

## Table of Contents
1. [Before You Update](#before-you-update)
2. [Update Methods](#update-methods)
3. [After Updating](#after-updating)
4. [Troubleshooting Updates](#troubleshooting-updates)
5. [Version Compatibility](#version-compatibility)

## Before You Update

### Check Current Version
```bash
cd /path/to/ani-downloader
git log --oneline -5
# or check version in app.py or README.md
```

### Backup Your Data
Always backup before updating:

```bash
# Create backup directory
mkdir backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

# Backup custom plugins
cp -r plugins/ $BACKUP_DIR/

# Backup downloads (optional, if space allows)
cp -r downloads/ $BACKUP_DIR/

# Backup configuration
cp config.json $BACKUP_DIR/
cp .env $BACKUP_DIR/ 2>/dev/null || true

# Backup database if using one
cp *.db $BACKUP_DIR/ 2>/dev/null || true
```

### Check Release Notes
Visit the [GitHub Releases page](https://github.com/your-repo/ani-downloader/releases) and read:
- Breaking changes
- New features
- Bug fixes
- Migration instructions

## Update Methods

### Method 1: Git Pull (Recommended for Git Users)

If you cloned the repository:

```bash
# Ensure you're on main branch
git checkout main

# Pull latest changes
git pull origin main

# Check for merge conflicts
git status

# If conflicts exist, resolve them
# Edit conflicting files, then:
git add <resolved-files>
git commit -m "Resolve merge conflicts"
```

### Method 2: Download Latest Release

If you downloaded a ZIP:

1. **Download the latest release** from GitHub
2. **Extract to a new directory**
3. **Copy your custom data** from the backup
4. **Replace the old installation**

```bash
# Download and extract
wget https://github.com/your-repo/ani-downloader/archive/refs/tags/v1.2.0.zip
unzip v1.2.0.zip
cd ani-downloader-1.2.0

# Copy your backups
cp -r ../backup_20231201/plugins/ plugins/
cp ../backup_20231201/config.json .
cp ../backup_20231201/.env . 2>/dev/null || true
```

### Method 3: Docker Update

For Docker installations:

```bash
# Stop containers
docker-compose down

# Pull latest images
docker-compose pull

# Start with new version
docker-compose up -d

# Check logs
docker-compose logs -f
```

## After Updating

### Update Dependencies
```bash
# Update Python packages
pip install -r requirements.txt

# If using virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Run Database Migrations (if applicable)
```bash
# Check if migration scripts exist
ls migrations/ 2>/dev/null || echo "No migrations directory"

# Run migrations if they exist
python manage.py migrate 2>/dev/null || echo "No migration command"
```

### Test the Application
```bash
# Start the application
python run.py

# Or with Docker
docker-compose up

# Test basic functionality
curl http://localhost:5000
```

### Verify Plugin Compatibility
```bash
# Test plugin loading
python -c "
from app.plugin_system import PluginManager
pm = PluginManager()
print(f'Loaded plugins: {len(pm.plugins)}')
for name, plugin in pm.plugins.items():
    print(f'- {name}: {plugin.name}')
"
```

### Update Configuration
Check if new configuration options are available:

```bash
# Compare with default config
diff config.json config.default.json 2>/dev/null || echo "No default config to compare"
```

## Troubleshooting Updates

### Merge Conflicts
If `git pull` shows conflicts:

```bash
# See conflicting files
git status

# Edit files to resolve conflicts
# Look for <<<<<<< HEAD, =======, >>>>>>> markers

# After resolving
git add <resolved-files>
git commit -m "Resolve update conflicts"
```

### Plugin Loading Issues
If plugins fail to load after update:

```bash
# Check plugin syntax
python -m py_compile plugins/your_plugin.py

# Test import
python -c "from plugins.your_plugin import YourPlugin; print('Import successful')"
```

### Dependency Issues
If packages fail to install:

```bash
# Upgrade pip
pip install --upgrade pip

# Clear cache and retry
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### Database Issues
If using a database:

```bash
# Backup database
cp app.db app.db.backup

# Reset if needed
rm app.db
python -c "from app import db; db.create_all()"
```

### Permission Issues
On Linux/Mac:

```bash
# Fix permissions
sudo chown -R $USER:$USER /path/to/ani-downloader
chmod +x run.py
```

### Docker Issues
```bash
# Clean up old containers
docker system prune

# Rebuild if needed
docker-compose build --no-cache
```

## Version Compatibility

### Breaking Changes by Version

#### v1.2.0
- Plugin interface updated: `get_video_data()` now returns dict instead of string
- New required method: `get_video_servers()`
- Configuration file format changed

#### v1.1.0
- Helper library introduced
- Plugin loading mechanism improved
- Search API updated

#### v1.0.0
- Initial release
- Basic plugin system

### Migration Scripts

For major version updates, run migration scripts:

```bash
# v1.1.x to v1.2.x migration
python migrations/v1_2_0_migrate.py

# v1.0.x to v1.1.x migration
python migrations/v1_1_0_migrate.py
```

## Automated Updates

### Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add weekly update check (every Monday at 2 AM)
0 2 * * 1 cd /path/to/ani-downloader && ./update.sh
```

### Update Script
Create `update.sh`:

```bash
#!/bin/bash
cd /path/to/ani-downloader

# Create backup
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir $BACKUP_DIR
cp -r plugins/ $BACKUP_DIR/
cp config.json $BACKUP_DIR/

# Update
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Test
python -c "from app import app; print('Update successful')" || {
    echo "Update failed, restoring backup"
    cp -r $BACKUP_DIR/plugins/ plugins/
    cp $BACKUP_DIR/config.json .
    exit 1
}

# Restart service
sudo systemctl restart ani-downloader
```

### Windows Scheduled Task
```powershell
# Create update.ps1
$script = @'
cd "C:\path\to\ani-downloader"
git pull origin main
& python -m pip install -r requirements.txt
& python run.py --test
'@

$script | Out-File -FilePath "C:\path\to\update.ps1"

# Create scheduled task
schtasks /create /tn "Ani-Downloader Update" /tr "powershell -File C:\path\to\update.ps1" /sc weekly /d MON /st 02:00
```

## Staying Updated

### Monitor Releases
- Watch the GitHub repository
- Subscribe to release notifications
- Follow development on social media

### Join Community
- Discord server
- Forums
- Reddit communities

### Beta Testing
- Test beta releases
- Report bugs
- Suggest features

## Emergency Rollback

If update breaks your installation:

```bash
# If using git
git log --oneline -10  # Find last working commit
git checkout <commit-hash>

# Restore from backup
cp -r backup_20231201/plugins/ plugins/
cp backup_20231201/config.json .

# Restart
python run.py
```

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/ani-downloader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ani-downloader/discussions)
- **Community**: [Discord/Forum link]

---

Remember: Always backup before updating, and test thoroughly after updating!