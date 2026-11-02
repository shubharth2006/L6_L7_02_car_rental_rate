import pytest

from car_rental_rate import check_fleet_telematics, process_rental_fleet


def test_process_rental_fleet_executes_all_application_lines():
    rentals = [
        {"is_confirmed": False},
        {"is_confirmed": True, "vehicle_type": "luxury", "driver_age": 24,
         "days": 2, "trip_segments": [100, 350]},
        {"is_confirmed": True, "vehicle_type": "suv", "driver_age": 30,
         "days": 1, "trip_segments": [-5, 300]},
        {"is_confirmed": True, "vehicle_type": "economy", "driver_age": 20,
         "days": 1, "trip_segments": [350]},
        {"is_confirmed": True, "days": 0},
    ]
    result = process_rental_fleet(rentals, 10)
    assert result["status"] == "STANDARD"
    assert result["total_revenue"] > 0


def test_process_rental_fleet_validates_arguments_and_terminal_statuses():
    with pytest.raises(ValueError):
        process_rental_fleet("not a list", 0)
    with pytest.raises(ValueError):
        process_rental_fleet([], -1)
    assert process_rental_fleet([], 0) == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}
    assert process_rental_fleet(
        [{"is_confirmed": True, "days": 0} for _ in range(5)], 0
    )["status"] == "HIGH_RISK_AUDIT"


def test_telematics_covers_no_data_safe_and_ground_paths():
    assert check_fleet_telematics([]) == "NO_DATA"
    assert check_fleet_telematics([[80, 101, 90], []]) == "SAFE"
    assert check_fleet_telematics([[101, 102]]) == "GROUND_VEHICLE"

