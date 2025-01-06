import logging

from flask import Flask, request, jsonify
from threading import Lock
from uuid import uuid4

from database.db import Session, configure_database
from database.models import Battery
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)

logger = logging.getLogger(__name__)

# Thread-safety transaction
batteries_lock = Lock()

@app.route("/<battery_id>", methods=["GET"])
def get_battery(battery_id):
    try:
        session = Session()

        query = session.query(Battery)
        battery = query.filter_by(battery_id=battery_id).one()

        return battery.to_dict(), 200

    except NoResultFound as e:
        logger.error(f"error: {e}, status code: 404")
        return jsonify({"error": "Battery instance not found"}), 404

    except Exception as e:
        logger.error(f"error: {e}, status code: 500")
        return jsonify({"error": str(e)}), 500

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

        with batteries_lock:
            session.add(battery)
            session.commit()

        return jsonify({
            "capacity_kwh": battery.capacity_kwh,
            "maximum_power_kw": battery.maximum_power_kw,
            "battery_id": battery.battery_id
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"error: {e}, status code: 500")
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

@app.route("/<battery_id>", methods=["DELETE"])
def delete_battery(battery_id):
    try:
        session = Session()

        query = session.query(Battery)
        battery = query.filter_by(battery_id=battery_id).one()

        with batteries_lock:
            session.delete(battery)
            session.commit()

        # Could have used 204 (No Content) but want to return additional response message.
        return jsonify({"message": f"Battery instance with ID: {battery_id} deleted successfully"}), 200

    except NoResultFound as e:
        logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
        return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404

    except Exception as e:
        session.rollback()
        logger.error(f"error: {e}, status code: 500")
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()

if __name__ == "__main__":
    configure_database()
    app.run(debug=True, port=8080)
