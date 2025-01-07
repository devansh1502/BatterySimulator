import logging

from flask import Flask, request, jsonify
from uuid import uuid4
from datetime import datetime

from database.db import Session, configure_database
from database.models import Battery

from src.octave_batteries import OctaveBattery

app = Flask(__name__)

logger = logging.getLogger(__name__)

@app.route("/<battery_id>", methods=["GET"])
def get_battery(battery_id):
    try:
        # TODO: can create decorators to start and terminate session
        session = Session()

        query = session.query(Battery)
        battery = query.filter_by(battery_id=battery_id).one_or_none()
        if battery is None:
            logger.error(f"error: {e}, status code: 404")
            return jsonify({"error": "Battery instance not found"}), 404

        return battery.to_dict(), 200

    except Exception as e:
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()

@app.route("/", methods=["POST"])
def create_battery():
    try:
        session = Session()

        data = request.json
        capacity = data.get("capacity_kwh")
        max_power = data.get("maximum_power_kw")

        if capacity is None or max_power is None:
            logger.error("Missing capacity_kwh or maximum_power_kw, status code: 400")
            return jsonify({"error": "Missing capacity_kwh or maximum_power_kw"}), 400

        battery = Battery(
            battery_id = str(uuid4()),
            capacity_kwh = capacity,
            maximum_power_kw= max_power
        )

        session.add(battery)
        session.commit()

        return jsonify({
            "capacity_kwh": battery.capacity_kwh,
            "maximum_power_kw": battery.maximum_power_kw,
            "battery_id": battery.battery_id
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()

@app.route("/<battery_id>", methods=["DELETE"])
def delete_battery(battery_id):
    try:
        session = Session()

        query = session.query(Battery)
        battery = query.filter_by(battery_id=battery_id).one_or_none()

        if battery is None:
            logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
            return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404

        session.delete(battery)
        session.commit()

        # Could have used 204 (No Content) but want to return additional response message.
        return jsonify({"message": f"Battery instance with ID: {battery_id} deleted successfully"}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()

# /update?battery_id=<id>&power=<int>&duration=<float>
@app.route("/update", methods=["PATCH"])
def update_battery():
    battery_id = request.args.get('battery_id', type=str)
    power = request.args.get('power', type=int)
    duration = request.args.get('duration', type=float)

    if battery_id is None or power is None or duration is None:
        logger.error("Missing battery_id, power or duration, status code: 400")
        return jsonify({"error": "Missing battery_id, power or duration"}), 400

    try:
        session = Session()

        query = session.query(Battery)
        battery_details = query.filter_by(battery_id=battery_id).one_or_none()

        print("battery_details", battery_details)

        if battery_details:
            if power > 0:
                battery_details = OctaveBattery.charge(battery_details, power, duration)
            elif power < 0:
                battery_details = OctaveBattery.discharge(battery_details, power, duration)


            warning = OctaveBattery.get_warning(battery_details)
            if warning:
                print("Warning: ", warning)
                print("timestamp: ", datetime.now().isoformat())
                # OctaveBattery.publish_warning(battery_details, warning)

            session.merge(battery_details)
            session.commit()

            return battery_details.to_dict(), 200
        else:
            logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
            return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404


    except Exception as e:
        session.rollback()
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

if __name__ == "__main__":
    configure_database()
    app.run(debug=True, port=8080)
