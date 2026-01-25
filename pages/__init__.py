"""
Page Object Model for Playwright browser automation.

Provides encapsulated page classes for clean, maintainable browser
interactions in UI load testing scenarios.
"""

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

__all__ = ["BasePage", "LoginPage", "DashboardPage"]
