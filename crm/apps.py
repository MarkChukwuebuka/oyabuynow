from django.apps import AppConfig


class CrmConfig(AppConfig):
    """
    Application configuration with signal registration
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = 'CRM'

    def ready(self):
        """
        Import signals when Django starts
        This ensures all signal handlers are registered
        """
        try:
            # Import signals module to register all signal handlers
            import crm.signals
            print("✓ Elasticsearch signals registered successfully")
        except ImportError as e:
            print(f"✗ Error importing signals: {str(e)}")
        except Exception as e:
            print(f"✗ Error registering signals: {str(e)}")