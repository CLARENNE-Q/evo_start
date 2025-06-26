# Multi-Vehicle Support Implementation

## Overview
The EVO-START Home Assistant integration has been successfully updated to support multiple vehicles. Previously, the integration only worked with the first vehicle returned by the API. Now, all vehicles associated with your EVO-START account are automatically discovered and configured.

## Key Changes Made

### 1. Coordinator (`coordinator.py`)
- **Changed**: `vehicle_data` and `flags` → `vehicles_data` and `vehicles_flags` (dictionaries indexed by vehicle ID)
- **Updated**: `get_vehicle_data()` → `get_vehicles_data()` to fetch all vehicles
- **Modified**: All remote action methods now accept `vehicle_id` parameter
- **Added**: Helper methods:
  - `get_vehicle_data(vehicle_id)` - Get data for specific vehicle
  - `get_vehicle_flags(vehicle_id)` - Get flags for specific vehicle  
  - `get_all_vehicle_ids()` - Get list of all vehicle IDs

### 2. Entity Classes
All entity classes updated to support multiple vehicles:

#### Sensors (`sensor.py`)
- Constructor now accepts `vehicle_id` and `vehicle_name`
- Unique IDs include vehicle ID: `evo_start_{vehicle_id}_{sensor_id}`
- Names include vehicle name: `EVO-START {vehicle_name} {sensor_name}`
- Device identifiers unique per vehicle: `evo_start_vehicle_{vehicle_id}`

#### Locks (`lock.py`)
- Same pattern as sensors
- Remote lock/unlock actions pass vehicle ID to coordinator

#### Buttons (`button.py`)
- Same pattern as sensors
- Remote start/stop actions pass vehicle ID to coordinator
- Availability checks use vehicle-specific flags

#### Device Tracker (`device_tracker.py`)
- Same pattern as sensors
- GPS coordinates and flags specific to each vehicle

### 3. Setup Functions
All `async_setup_entry` functions updated to:
- Loop through all vehicle IDs from coordinator
- Create entities for each vehicle
- Extract vehicle name from API data for entity naming

### 4. Documentation (`README.md`)
- Updated features to highlight multi-vehicle support
- Modified entity tables to show vehicle name placeholders
- Updated technical notes
- Marked multi-vehicle support as completed

### 5. Version Updates
- `manifest.json`: Version bumped to 2.0.0
- `hacs.json`: Version bumped to 2.0.0, added button domain

## Benefits

1. **Automatic Discovery**: All vehicles in your account are automatically detected
2. **Separate Devices**: Each vehicle appears as a separate device in Home Assistant
3. **Clear Naming**: Entity names include vehicle names for easy identification
4. **Independent Control**: Each vehicle can be controlled independently
5. **Backward Compatible**: Single vehicle setups work the same way

## Entity Naming Examples

For a vehicle named "My Tesla Model 3":
- `sensor.evo_start_my_tesla_model_3_battery_voltage`
- `lock.evo_start_my_tesla_model_3_central_lock`
- `button.evo_start_my_tesla_model_3_remote_start`
- `device_tracker.evo_start_my_tesla_model_3`

## Testing Recommendations

1. Test with single vehicle account (should work as before)
2. Test with multiple vehicle account (should create separate entities)
3. Verify all remote actions work for each vehicle
4. Check that entity names are clear and distinguishable
5. Ensure device tracker coordinates are correct for each vehicle
