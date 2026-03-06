from dataclasses import dataclass


@dataclass(frozen=True)
class LoginSelectors:
    # TODO: Replace with real locators from your app (prefer role/label)
    username_input_label: str = "Email address *"
    password_input_label: str = "Password *"
    continue_button_name: str = "Continue"


@dataclass(frozen=True)
class AppReadySelectors:
    # TODO: Pick something that exists only after successful login
    landing_unique_role: str = "link"
    landing_unique_name: str = "Programs"


login_sel = LoginSelectors()
ready_sel = AppReadySelectors()
