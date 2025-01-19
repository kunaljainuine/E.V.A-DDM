from abc import ABC, abstractmethod
import importlib
import os
import logging
from typing import Dict, Type, Any
from Backend.Config import config

logger = logging.getLogger("PluginSystem")

class Plugin(ABC):
    """Base class for all plugins"""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup any resources used by the plugin"""
        pass

class PluginManager:
    """Manages the loading and execution of plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Type[Plugin]] = {}
        self.active_plugins: Dict[str, Plugin] = {}
        logger.info("Plugin Manager initialized")
    
    def discover_plugins(self, plugin_dir: str = "Backend/Plugins") -> None:
        """
        Discover and register all plugins in the specified directory
        
        Args:
            plugin_dir (str): Directory containing plugin modules
        """
        try:
            logger.info(f"Discovering plugins in {plugin_dir}")
            
            # Ensure plugin directory exists
            if not os.path.exists(plugin_dir):
                os.makedirs(plugin_dir)
                logger.debug(f"Created plugin directory: {plugin_dir}")
            
            # Import all python files in the plugin directory
            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]  # Remove .py extension
                    try:
                        # Import the module
                        module = importlib.import_module(f"Backend.Plugins.{module_name}")
                        
                        # Find all Plugin subclasses in the module
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                issubclass(attr, Plugin) and 
                                attr != Plugin):
                                self.register_plugin(module_name, attr)
                                
                    except Exception as e:
                        logger.error(f"Error loading plugin {module_name}: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}", exc_info=True)
    
    def register_plugin(self, name: str, plugin_class: Type[Plugin]) -> None:
        """
        Register a new plugin
        
        Args:
            name (str): Name of the plugin
            plugin_class (Type[Plugin]): Plugin class to register
        """
        try:
            logger.info(f"Registering plugin: {name}")
            self.plugins[name] = plugin_class
        except Exception as e:
            logger.error(f"Error registering plugin {name}: {e}", exc_info=True)
    
    def initialize_plugin(self, name: str) -> None:
        """
        Initialize a registered plugin
        
        Args:
            name (str): Name of the plugin to initialize
        """
        try:
            if name not in self.plugins:
                raise ValueError(f"Plugin {name} not found")
            
            logger.info(f"Initializing plugin: {name}")
            plugin = self.plugins[name]()
            plugin.initialize()
            self.active_plugins[name] = plugin
            
        except Exception as e:
            logger.error(f"Error initializing plugin {name}: {e}", exc_info=True)
            raise
    
    def execute_plugin(self, name: str, *args, **kwargs) -> Any:
        """
        Execute a plugin
        
        Args:
            name (str): Name of the plugin to execute
            *args: Positional arguments to pass to the plugin
            **kwargs: Keyword arguments to pass to the plugin
            
        Returns:
            Any: Result from plugin execution
        """
        try:
            if name not in self.active_plugins:
                self.initialize_plugin(name)
                
            logger.debug(f"Executing plugin: {name}")
            return self.active_plugins[name].execute(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error executing plugin {name}: {e}", exc_info=True)
            raise
    
    def cleanup_plugin(self, name: str) -> None:
        """
        Cleanup a plugin's resources
        
        Args:
            name (str): Name of the plugin to cleanup
        """
        try:
            if name in self.active_plugins:
                logger.info(f"Cleaning up plugin: {name}")
                self.active_plugins[name].cleanup()
                del self.active_plugins[name]
                
        except Exception as e:
            logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
            
    def cleanup_all(self) -> None:
        """Cleanup all active plugins"""
        try:
            logger.info("Cleaning up all plugins")
            for name in list(self.active_plugins.keys()):
                self.cleanup_plugin(name)
                
        except Exception as e:
            logger.error(f"Error cleaning up plugins: {e}", exc_info=True)

# Example usage:
if __name__ == "__main__":
    # Initialize plugin manager
    plugin_manager = PluginManager()
    
    # Discover and load plugins
    plugin_manager.discover_plugins()
    
    try:
        # Execute plugins as needed
        for plugin_name in plugin_manager.plugins:
            result = plugin_manager.execute_plugin(plugin_name)
            print(f"Plugin {plugin_name} result: {result}")
            
    finally:
        # Cleanup
        plugin_manager.cleanup_all() 