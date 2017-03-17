"""
Sets up a demo environment that mimics interaction with devices.

For more details about this component, please refer to the documentation
https://home-assistant.io/components/demo/
"""
import time

import homeassistant.bootstrap as bootstrap
import homeassistant.core as ha
import homeassistant.loader as loader
from homeassistant.const import ATTR_ENTITY_ID, CONF_PLATFORM

DEPENDENCIES = ['conversation', 'introduction', 'zone']
DOMAIN = 'demo'

COMPONENTS_WITH_DEMO_PLATFORM = [
    'alarm_control_panel',
    'binary_sensor',
    'calendar',
    'camera',
    'climate',
    'cover',
    'device_tracker',
    'fan',
    'light',
    'lock',
    'media_player',
    'notify',
    'sensor',
    'switch',
]


def setup(hass, config):
    """Setup a demo environment."""
    group = loader.get_component('group')
    configurator = loader.get_component('configurator')
    persistent_notification = loader.get_component('persistent_notification')

    config.setdefault(ha.DOMAIN, {})
    config.setdefault(DOMAIN, {})

    if config[DOMAIN].get('hide_demo_state') != 1:
        hass.states.set('a.Demo_Mode', 'Enabled')

    # Setup sun
    if not hass.config.latitude:
        hass.config.latitude = 32.87336

    if not hass.config.longitude:
        hass.config.longitude = 117.22743

    bootstrap.setup_component(hass, 'sun')

    # Setup demo platforms
    demo_config = config.copy()
    for component in COMPONENTS_WITH_DEMO_PLATFORM:
        demo_config[component] = {CONF_PLATFORM: 'demo'}
        bootstrap.setup_component(hass, component, demo_config)

    # Setup example persistent notification
    persistent_notification.create(
        hass, 'This is an example of a persistent notification.',
        title='Example Notification')

    # Setup room groups
    lights = sorted(hass.states.entity_ids('light'))
    switches = sorted(hass.states.entity_ids('switch'))
    media_players = sorted(hass.states.entity_ids('media_player'))

    group.Group.create_group(hass, 'living room', [
        lights[1], switches[0], 'input_select.living_room_preset',
        'rollershutter.living_room_window', media_players[1],
        'scene.romantic_lights'])
    group.Group.create_group(hass, 'bedroom', [
        lights[0], switches[1], media_players[0],
        'input_slider.noise_allowance'])
    group.Group.create_group(hass, 'kitchen', [
        lights[2], 'rollershutter.kitchen_window', 'lock.kitchen_door'])
    group.Group.create_group(hass, 'doors', [
        'lock.front_door', 'lock.kitchen_door',
        'garage_door.right_garage_door', 'garage_door.left_garage_door'])
    group.Group.create_group(hass, 'automations', [
        'input_select.who_cooks', 'input_boolean.notify', ])
    group.Group.create_group(hass, 'people', [
        'device_tracker.demo_anne_therese', 'device_tracker.demo_home_boy',
        'device_tracker.demo_paulus'])
    group.Group.create_group(hass, 'downstairs', [
        'group.living_room', 'group.kitchen',
        'scene.romantic_lights', 'rollershutter.kitchen_window',
        'rollershutter.living_room_window', 'group.doors',
        'thermostat.ecobee',
    ], view=True)

    # Setup scripts
    bootstrap.setup_component(
        hass, 'script',
        {'script': {
            'demo': {
                'alias': 'Toggle {}'.format(lights[0].split('.')[1]),
                'sequence': [{
                    'service': 'light.turn_off',
                    'data': {ATTR_ENTITY_ID: lights[0]}
                }, {
                    'delay': {'seconds': 5}
                }, {
                    'service': 'light.turn_on',
                    'data': {ATTR_ENTITY_ID: lights[0]}
                }, {
                    'delay': {'seconds': 5}
                }, {
                    'service': 'light.turn_off',
                    'data': {ATTR_ENTITY_ID: lights[0]}
                }]
            }}})

    # Setup scenes
    bootstrap.setup_component(
        hass, 'scene',
        {'scene': [
            {'name': 'Romantic lights',
             'entities': {
                 lights[0]: True,
                 lights[1]: {'state': 'on', 'xy_color': [0.33, 0.66],
                             'brightness': 200},
             }},
            {'name': 'Switch on and off',
             'entities': {
                 switches[0]: True,
                 switches[1]: False,
             }},
            ]})

    # Set up input select
    bootstrap.setup_component(
        hass, 'input_select',
        {'input_select':
         {'living_room_preset': {'options': ['Visitors',
                                             'Visitors with kids',
                                             'Home Alone']},
          'who_cooks': {'icon': 'mdi:panda',
                        'initial': 'Anne Therese',
                        'name': 'Cook today',
                        'options': ['Paulus', 'Anne Therese']}}})
    # Set up input boolean
    bootstrap.setup_component(
        hass, 'input_boolean',
        {'input_boolean': {'notify': {'icon': 'mdi:car',
                                      'initial': False,
                                      'name': 'Notify Anne Therese is home'}}})

    # Set up input boolean
    bootstrap.setup_component(
        hass, 'input_slider',
        {'input_slider': {
            'noise_allowance': {'icon': 'mdi:bell-ring',
                                'min': 0,
                                'max': 10,
                                'name': 'Allowed Noise',
                                'unit_of_measurement': 'dB'}}})

    # Set up weblink
    bootstrap.setup_component(
        hass, 'weblink',
        {'weblink': {'entities': [{'name': 'Router',
                                   'url': 'http://192.168.1.1'}]}})
    # Setup configurator
    configurator_ids = []

    def hue_configuration_callback(data):
        """Fake callback, mark config as done."""
        time.sleep(2)

        # First time it is called, pretend it failed.
        if len(configurator_ids) == 1:
            configurator.notify_errors(
                configurator_ids[0],
                "Failed to register, please try again.")

            configurator_ids.append(0)
        else:
            configurator.request_done(configurator_ids[0])

    request_id = configurator.request_config(
        hass, "Philips Hue", hue_configuration_callback,
        description=("Press the button on the bridge to register Philips Hue "
                     "with Home Assistant."),
        description_image="/static/images/config_philips_hue.jpg",
        submit_caption="I have pressed the button"
    )

    configurator_ids.append(request_id)

    return True
