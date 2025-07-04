"""CPU monitoring and adaptive throttling utilities."""

import asyncio

import psutil

from ..common.logger import logger


class CPUMonitor:
    """Monitor CPU usage and provide adaptive throttling."""
    
    def __init__(self, 
                 target_cpu_percent: float = 50.0,
                 check_interval: float = 1.0):
        """
        Initialize CPU monitor.
        
        Args:
            target_cpu_percent: Target CPU usage percentage
            check_interval: How often to check CPU usage
        """
        self.target_cpu_percent = target_cpu_percent
        self.check_interval = check_interval
        self._current_cpu_percent: float | None = None
        self._monitoring_task: asyncio.Task | None = None
    
    async def start(self):
        """Start monitoring CPU usage."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_loop())
            logger.info("CPU monitoring started", target_cpu=self.target_cpu_percent)
    
    async def stop(self):
        """Stop monitoring CPU usage."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("CPU monitoring stopped")
    
    async def _monitor_loop(self):
        """Background task to monitor CPU usage."""
        while True:
            try:
                # Get CPU usage over the interval
                self._current_cpu_percent = psutil.cpu_percent(interval=self.check_interval)
                
                if self._current_cpu_percent > 80:
                    logger.warning(
                        "High CPU usage detected",
                        cpu_percent=self._current_cpu_percent
                    )
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error monitoring CPU", error=str(e))
                await asyncio.sleep(self.check_interval)
    
    def get_throttle_delay(self, base_delay: float = 0.1) -> float:
        """
        Calculate throttle delay based on current CPU usage.
        
        Args:
            base_delay: Base delay in seconds
            
        Returns:
            Adjusted delay time
        """
        if self._current_cpu_percent is None:
            return base_delay
        
        # If CPU is below target, use base delay
        if self._current_cpu_percent <= self.target_cpu_percent:
            return base_delay
        
        # Scale delay based on how much we're over target
        # For every 10% over target, double the delay
        over_target = self._current_cpu_percent - self.target_cpu_percent
        multiplier = 1 + (over_target / 10)
        
        adjusted_delay = base_delay * multiplier
        
        # Cap at 2 seconds max delay
        return min(adjusted_delay, 2.0)
    
    def should_pause(self) -> bool:
        """
        Check if processing should pause due to high CPU.
        
        Returns:
            True if CPU usage is critically high (>90%)
        """
        if self._current_cpu_percent is None:
            return False
        
        return self._current_cpu_percent > 90
    
    async def wait_for_cpu(self, max_wait: float = 30.0):
        """
        Wait for CPU usage to drop below critical levels.
        
        Args:
            max_wait: Maximum time to wait in seconds
        """
        start_time = asyncio.get_event_loop().time()
        
        while self.should_pause():
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                logger.warning("CPU wait timeout exceeded", elapsed=elapsed)
                break
            
            logger.info(
                "Waiting for CPU to cool down",
                cpu_percent=self._current_cpu_percent,
                elapsed=elapsed
            )
            await asyncio.sleep(2.0)


# Global CPU monitor instance
cpu_monitor = CPUMonitor()