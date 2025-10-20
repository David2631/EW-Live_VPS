"""
VPS Trading System Monitor
Real-time monitoring and alerting for Elliott Wave trading system
"""

import time
import psutil
import json
import logging
import smtplib
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import subprocess
import os

class TradingSystemMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Load monitoring configuration"""
        default_config = {
            "check_interval": 300,  # 5 minutes
            "max_cpu_usage": 80,
            "max_memory_usage": 80,
            "max_response_time": 10,
            "restart_on_failure": True,
            "email_alerts": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your_email@gmail.com",
                "password": "your_app_password",
                "recipients": ["your_email@gmail.com"]
            },
            "trading_system": {
                "script_name": "elliott_live_trader.py",
                "max_restart_attempts": 3,
                "restart_delay": 60
            }
        }
        
        config_file = "monitor_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    # Merge configs
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        else:
            # Create default config file
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config: {config_file}")
            
        return default_config
    
    def setup_logging(self):
        """Setup monitoring logs"""
        log_filename = f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_system_health(self):
        """Check overall system health"""
        try:
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                "trading_process_running": self.is_trading_process_running(),
                "system_uptime": self.get_system_uptime()
            }
            return health_report
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return None
    
    def is_trading_process_running(self):
        """Check if trading process is running"""
        script_name = self.config['trading_system']['script_name']
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any(script_name in cmd for cmd in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error checking trading process: {e}")
        return False
    
    def get_system_uptime(self):
        """Get system uptime in hours"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return round(uptime_seconds / 3600, 1)  # Convert to hours
        except:
            return 0
    
    def restart_trading_system(self):
        """Restart the trading system"""
        if not self.config.get('restart_on_failure', False):
            return False
            
        script_name = self.config['trading_system']['script_name']
        max_attempts = self.config['trading_system']['max_restart_attempts']
        restart_delay = self.config['trading_system']['restart_delay']
        
        self.logger.info(f"Attempting to restart {script_name}")
        
        for attempt in range(max_attempts):
            try:
                # Start the trading system
                if os.name == 'nt':  # Windows
                    subprocess.Popen([
                        'python', script_name
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # Linux/Mac
                    subprocess.Popen(['python', script_name])
                
                # Wait and check if it started
                time.sleep(restart_delay)
                if self.is_trading_process_running():
                    self.logger.info(f"Successfully restarted {script_name}")
                    return True
                else:
                    self.logger.warning(f"Restart attempt {attempt + 1} failed")
                    
            except Exception as e:
                self.logger.error(f"Error restarting system: {e}")
                
        self.logger.error(f"Failed to restart {script_name} after {max_attempts} attempts")
        return False
    
    def send_alert(self, subject, message):
        """Send email alert"""
        if not self.config['email_alerts']['enabled']:
            return False
            
        try:
            msg = MimeMultipart()
            msg['From'] = self.config['email_alerts']['username']
            msg['To'] = ', '.join(self.config['email_alerts']['recipients'])
            msg['Subject'] = f"[Elliott Wave VPS Alert] {subject}"
            
            body = f"""
Elliott Wave Trading System Alert

{message}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: VPS Trading Monitor
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(
                self.config['email_alerts']['smtp_server'],
                self.config['email_alerts']['smtp_port']
            )
            server.starttls()
            server.login(
                self.config['email_alerts']['username'],
                self.config['email_alerts']['password']
            )
            
            text = msg.as_string()
            server.sendmail(
                self.config['email_alerts']['username'],
                self.config['email_alerts']['recipients'],
                text
            )
            server.quit()
            
            self.logger.info(f"Alert sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False
    
    def run_monitoring(self):
        """Run continuous monitoring"""
        print("🔍 Starting Elliott Wave VPS Trading System Monitor...")
        print(f"📊 Monitoring interval: {self.config['check_interval']} seconds")
        print(f"📧 Email alerts: {'Enabled' if self.config['email_alerts']['enabled'] else 'Disabled'}")
        print("🚨 Press Ctrl+C to stop monitoring")
        print("-" * 60)
        
        restart_attempts = 0
        max_restart_attempts = self.config['trading_system']['max_restart_attempts']
        
        while True:
            try:
                health = self.check_system_health()
                if not health:
                    time.sleep(60)  # Wait 1 minute on error
                    continue
                
                # Log current status
                self.logger.info(
                    f"Health: CPU={health['cpu_usage']:.1f}% "
                    f"MEM={health['memory_usage']:.1f}% "
                    f"DISK={health['disk_usage']:.1f}% "
                    f"Trading={'ON' if health['trading_process_running'] else 'OFF'} "
                    f"Uptime={health['system_uptime']}h"
                )
                
                # Check for alerts
                alerts = []
                
                if health['cpu_usage'] > self.config['max_cpu_usage']:
                    alerts.append(f"High CPU usage: {health['cpu_usage']:.1f}%")
                
                if health['memory_usage'] > self.config['max_memory_usage']:
                    alerts.append(f"High memory usage: {health['memory_usage']:.1f}%")
                
                if health['disk_usage'] > 90:
                    alerts.append(f"High disk usage: {health['disk_usage']:.1f}%")
                
                if not health['trading_process_running']:
                    alerts.append("Trading process not running!")
                    
                    # Attempt to restart if enabled
                    if self.config.get('restart_on_failure', False) and restart_attempts < max_restart_attempts:
                        restart_attempts += 1
                        self.logger.warning(f"Attempting restart #{restart_attempts}")
                        if self.restart_trading_system():
                            alerts.append(f"Trading system restarted successfully (attempt {restart_attempts})")
                            restart_attempts = 0  # Reset counter on success
                        else:
                            alerts.append(f"Failed to restart trading system (attempt {restart_attempts})")
                else:
                    restart_attempts = 0  # Reset counter when system is running
                
                # Send alerts
                if alerts:
                    alert_message = "\n".join(alerts)
                    self.send_alert("System Alert", alert_message)
                    print(f"⚠️  ALERT: {alert_message}")
                else:
                    status_msg = (f"✅ System healthy: CPU={health['cpu_usage']:.1f}% "
                                f"MEM={health['memory_usage']:.1f}% "
                                f"Trading={'ON' if health['trading_process_running'] else 'OFF'}")
                    print(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
                
                time.sleep(self.config['check_interval'])
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute on error

def main():
    """Main monitoring function"""
    monitor = TradingSystemMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()