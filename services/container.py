"""
Dependency injection container for service management.

This module provides a lightweight dependency injection container that manages
service registration, instantiation, and dependency resolution. It supports
both factory-based registration and direct instance registration.

The container automatically resolves constructor dependencies using type
annotations, enabling clean separation of concerns and improved testability.

Classes:
    DIContainer: Main dependency injection container

Features:
    - Automatic constructor dependency injection
    - Singleton service instances
    - Type-based service resolution
    - Factory and instance registration
"""

from typing import Dict, Type, Any, Callable
import inspect

class DIContainer:
    """
    Lightweight dependency injection container with automatic dependency resolution.

    Manages service registration and instantiation with automatic constructor
    dependency injection. Services are registered by interface type and resolved
    as singletons, ensuring consistent instances throughout the application.

    The container uses Python's type annotations to automatically resolve
    constructor dependencies, eliminating the need for manual wiring.

    Attributes:
        _services: Cache of instantiated service instances
        _factories: Registry of service factory classes

    Example:
        >>> container = DIContainer()
        >>> container.register(ServiceInterface, ServiceImplementation)
        >>> service = container.get(ServiceInterface)
        >>> isinstance(service, ServiceImplementation)
        True
    """

    def __init__(self) -> None:
        """
        Initialize the dependency injection container.

        Creates empty registries for services and factories.
        """
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register(self, interface: Type, implementation: Type) -> None:
        """
        Register a service implementation for an interface.

        Associates an interface type with a concrete implementation class.
        The implementation will be instantiated on first request with
        automatic dependency injection.

        Args:
            interface: Abstract interface or base class type
            implementation: Concrete implementation class

        Example:
            >>> container.register(PolicyParserInterface, PolicyParser)
        """
        self._factories[interface.__name__] = implementation

    def register_instance(self, interface: Type, instance: Any) -> None:
        """
        Register a pre-instantiated service instance.

        Directly registers a service instance, bypassing factory instantiation.
        Useful for registering configured objects or external dependencies.

        Args:
            interface: Interface type for service lookup
            instance: Pre-instantiated service object

        Example:
            >>> parser = PolicyParser("custom_policy.json")
            >>> container.register_instance(PolicyParserInterface, parser)
        """
        self._services[interface.__name__] = instance

    def get(self, interface: Type) -> Any:
        """
        Get service instance with automatic dependency injection.

        Retrieves or creates a service instance for the specified interface.
        If the service hasn't been instantiated, creates it using the
        registered factory with automatic constructor dependency resolution.

        Services are cached as singletons - subsequent requests return
        the same instance.

        Args:
            interface: Interface type to resolve

        Returns:
            Any: Service instance implementing the interface

        Raises:
            ValueError: If no service is registered for the interface

        Example:
            >>> parser = container.get(PolicyParserInterface)
            >>> graph = container.get(NetworkGraphInterface)  # Auto-injected with parser
        """
        service_name = interface.__name__

        if service_name in self._services:
            return self._services[service_name]

        if service_name in self._factories:
            factory = self._factories[service_name]

            # Get constructor parameters
            sig = inspect.signature(factory.__init__)
            params = {}

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Try to resolve parameter by type annotation
                if param.annotation != inspect.Parameter.empty:
                    try:
                        params[param_name] = self.get(param.annotation)
                    except KeyError:
                        # If we can't resolve the dependency, skip it
                        # This allows for optional dependencies
                        pass

            # Create instance with resolved dependencies
            instance = factory(**params)
            self._services[service_name] = instance
            return instance

        raise KeyError(f"Service {service_name} not registered")

    def clear(self):
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
