# Track Conditions
This is an app for Assetto Corsa, a racing simulator built by Kunos Simulazioni. It provides the user with a live wind indicator, as well as information on the wind speed, ambient temperature, track temperature and track grip state.

![Screenshot](assets/app_preview.png)

## Installation guide
Install the app by pasting the contents of the .zip file in the main root folder of the Assetto Corsa installation. After this, the app must be activated in the main menu within Assetto Corsa.

## Configuration
The app is user configurable and is integrated with Content Manager. After first launch, options like app size can be tweaked using the config.ini file in the app folder or through Content Manager.

## Wind Indicator
By default, the indicator acts as a wind vane for the true wind: It points into the wind, relative to the direction the car is facing. For example, if the vane is pointing downwards, that means the true wind is coming from behind: the car experiences a tailwind. The true wind is the wind that is experienced when stationary; the headwind that results from moving is excluded.

The wind indicator is color-coded. It shows green for a headwind, yellow for a crosswind and red for a tailwind. A headwind associated with green because the car has increased downforce.

The wind indicator functionality is user configurable. If you wish that the wind indicator acts as an arrow that points where the wind is going, rather than toward the source, you can choose this in the config.

## Notes
In replay mode, there is no accurate data available from the simulator. To avoid displaying wrong information, the wind indicator gets greyed out and other data fields are presented empty.