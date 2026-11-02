import pytest

from car_rental_rate import check_fleet_telematics, process_rental_fleet


@pytest.mark.parametrize(
    "rentals, fee, expected",
    [
        ("bad", 0, ValueError),
        ([], -1, ValueError),
        ([], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
        ([{"is_confirmed": False}], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
        ([{"is_confirmed": True, "days": 0}], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
        ([{"is_confirmed": True, "days": 0} for _ in range(5)], 0,
         {"total_revenue": 0.0, "status": "HIGH_RISK_AUDIT"}),
    ],
)
def test_input_and_final_status_branches(rentals, fee, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            process_rental_fleet(rentals, fee)
    else:
        assert process_rental_fleet(rentals, fee) == expected


@pytest.mark.parametrize(
    "vehicle_type, age, days, segments, expected_total",
    [
        ("luxury", 30, 2, [], 250.0),
        ("suv", 30, 2, [300], 210.0),
        ("economy", 30, 2, [301], 210.4),
        ("other", 24, 1, [0], 70.0),
        ("luxury", 24, 2, [0], 350.0),
        ("economy", 20, 1, [350], 320.0),
        ("suv", 30, 1, [-1, 1], 80.2),
    ],
)
def test_rental_pricing_and_trip_branches(vehicle_type, age, days, segments, expected_total):
    result = process_rental_fleet(
        [{"is_confirmed": True, "vehicle_type": vehicle_type, "driver_age": age,
          "days": days, "trip_segments": segments}], 10
    )
    assert result["total_revenue"] == expected_total
    assert result["status"] == "STANDARD"


def test_telematics_all_decision_branches():
    assert check_fleet_telematics(None) == "NO_DATA"
    assert check_fleet_telematics([[]]) == "SAFE"
    assert check_fleet_telematics([[101, 99, 101, 100]]) == "SAFE"
    assert check_fleet_telematics([[101, 102]]) == "GROUND_VEHICLE"

