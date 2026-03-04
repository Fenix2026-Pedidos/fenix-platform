import os
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from django.template import TemplateSyntaxError
from django.conf import settings
from django.template.utils import get_app_template_dirs

class Command(BaseCommand):
    help = 'Compile all HTML templates to catch syntax errors before deployment'

    def handle(self, *args, **options):
        self.stdout.write("Starting template compilation test...")
        
        template_dirs = []
        for engine in settings.TEMPLATES:
            if 'DIRS' in engine:
                template_dirs.extend(engine['DIRS'])
        
        # Add app template dirs
        template_dirs.extend(get_app_template_dirs('templates'))

        errors = []
        templates_checked = []

        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith('.html'):
                        rel_dir = os.path.relpath(root, template_dir)
                        if rel_dir == '.':
                            template_name = file
                        else:
                            template_name = os.path.join(rel_dir, file).replace('\\', '/')
                        
                        # Prevent duplicate checks
                        if template_name in templates_checked:
                            continue
                            
                        templates_checked.append(template_name)
                        
                        try:
                            # This actually parses and compiles the template
                            get_template(template_name)
                        except TemplateSyntaxError as e:
                            errors.append(f"SyntaxError in {template_name}: {str(e)}")
                        except Exception as e:
                            # Catch undefined tags, blocks, etc.
                            err_str = str(e)
                            if "is not a registered tag library" in err_str or "Invalid block tag" in err_str:
                                errors.append(f"Template parsing error in {template_name}: {err_str}")

        if errors:
            self.stdout.write(self.style.ERROR(f"Checked {len(templates_checked)} templates. Found {len(errors)} ERROR(S):"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f" ❌ {err}"))
            raise CommandError("Template compilation STOPPED due to syntax errors.")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully compiled {len(templates_checked)} templates. No syntax errors found."))
