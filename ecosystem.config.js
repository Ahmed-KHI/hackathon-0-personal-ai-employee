module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'orchestrator_claude.py',
      interpreter: 'python',
      cwd: './',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/orchestrator_error.log',
      out_file: './logs/orchestrator_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'watcher-filesystem',
      script: 'watcher_filesystem.py',
      interpreter: 'python',
      cwd: './',
      instances: 1,
      autorestart: true,
      watch: false,
      error_file: './logs/watcher_filesystem_error.log',
      out_file: './logs/watcher_filesystem_out.log'
    },
    {
      name: 'watcher-gmail',
      script: 'watcher_gmail.py',
      interpreter: 'python',
      cwd: './',
      instances: 1,
      autorestart: true,
      watch: false,
      error_file: './logs/watcher_gmail_error.log',
      out_file: './logs/watcher_gmail_out.log'
    },
    {
      name: 'watcher-linkedin',
      script: 'watcher_linkedin.py',
      interpreter: 'python',
      cwd: './',
      instances: 1,
      autorestart: true,
      watch: false,
      error_file: './logs/watcher_linkedin_error.log',
      out_file: './logs/watcher_linkedin_out.log'
    }
  ]
};
