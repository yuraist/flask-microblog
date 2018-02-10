#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand, Migrate

# Configure an app manager
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    """Import key instances for shell debugging"""
    return dict(app=app, db=db, User=User, Role=Role)


# Add commands to the application manager
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    from flask_migrate import upgrade
    from app.models import User, Role

    # Migrate database to the last version
    upgrade()

    # Create user roles
    Role.insert_roles()

    # Ensure all users are following themselves
    User.add_self_follows()


if __name__ == '__main__':
    # Run the app
    manager.run()
