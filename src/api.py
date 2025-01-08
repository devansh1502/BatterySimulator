from uuid import uuid4

from flask import Flask, jsonify, request
from pydantic import ValidationError

from database.db import Session
from database.models import Battery, CreateBattery, UpdateBattery
from src.octave_batteries import OctaveBattery
from utils.utils import logger

app = Flask(__name__)


@app.route("/get", methods=["GET"])
def get_all_batteries():
    try:
        session = Session()
        query = session.query(Battery)
        limit = request.args.get("limit", type=int, default=10)
        offset = request.args.get("offset", type=int, default=0)

        total = query.count()  # counting total values before setting limit and offset
        query = query.limit(limit).offset(offset)  # setting limit and offset

        rows = query.all()
        batteries = [b.to_dict() for b in rows]

        next_offset = offset + limit  # setting next offset
        next_link = None
        if next_offset < total:
            next_link = f"?limit={limit}&offset={next_offset}"

        return jsonify({
            "total": total,
            "limit": limit,
            "offset": offset,
            "next": next_link,
            "batteries": batteries
        }), 200

    except Exception as e:
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()


@app.route("/<battery_id>", methods=["GET"])
def get_battery(battery_id):
    try:
        session = Session()

        query = session.query(Battery)
        battery = query.filter_by(battery_id=battery_id).one_or_none()
        if battery is None:
            logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
            return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404

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
        validated = CreateBattery(**data)

        battery = Battery(
            battery_id=str(uuid4()),
            capacity_kwh=validated.capacity_kwh,
            maximum_power_kw=validated.maximum_power_kw,
        )

        session.add(battery)
        session.commit()

        return jsonify({
            "capacity_kwh": battery.capacity_kwh,
            "maximum_power_kw": battery.maximum_power_kw,
            "battery_id": battery.battery_id
        }), 201

    except ValidationError as ve:
        logger.error(f"error: Missing or incorrect required fields. Details: {ve}, status code: 400")
        return jsonify({"error": f"Missing or incorrect required fields. Details: {str(ve)}"}), 400

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

        return jsonify({"message": f"Battery instance with ID: {battery_id} deleted successfully"}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()


@app.route("/update", methods=["PATCH"])
def update_battery():
    try:
        data = {
            "battery_id": request.args.get("battery_id", type=str),
            "power": request.args.get("power", type=int),
            "duration": request.args.get("duration", type=int),
        }
        validated = UpdateBattery(**data)

        duration_in_hours = validated.duration / 60  # Converting minutes to hours
        session = Session()

        query = session.query(Battery)
        battery_details = query.filter_by(battery_id=validated.battery_id).one_or_none()
        if battery_details is None:
            logger.error(f"error: Could not find the battery with ID: {validated.battery_id}, status code: 404")
            return jsonify({"error": f"Could not find the battery with ID: {validated.battery_id}"}), 404


        ob = OctaveBattery(
            battery_details.battery_id,
            battery_details.capacity_kwh,
            battery_details.maximum_power_kw,
            battery_details.state_of_charge,
            battery_details.cycles,
        )
        if validated.power > 0:
            ob.charge(validated.power, duration_in_hours)
        elif validated.power < 0:
            ob.discharge(validated.power, duration_in_hours)

        ob.check_warning()  # checking and publishing warning if any

        battery_details.battery_id = ob.battery_id
        battery_details.capacity_kwh = ob.capacity_kwh
        battery_details.maximum_power_kw = ob.maximum_power_kw
        battery_details.state_of_charge = ob.state_of_charge
        battery_details.cycles = ob.cycles

        session.merge(battery_details)
        session.commit()

        return battery_details.to_dict(), 200

    except ValidationError as ve:
        logger.error(f"error: Missing or incorrect required fields. Details: {ve}, status code: 400")
        return jsonify({"error": f"Missing or incorrect required fields. Details: {str(ve)}"}), 400

    except Exception as e:
        session.rollback()
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500


@app.route("/soc", methods=["GET"])
def get_soc():
    battery_id = request.args.get("battery_id", type=str)
    try:
        session = Session()
        query = session.query(Battery)

        if battery_id:
            battery = query.filter_by(battery_id=battery_id).one_or_none()

            if battery is None:
                logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
                return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404

            return jsonify({
                "battery_id": battery_id,
                "soc": battery.state_of_charge
                }), 200
        else:
            batteries = query.all()
            return jsonify([
                {"battery_id": b.battery_id, "soc": b.state_of_charge} for b in batteries
            ]), 200

    except Exception as e:
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()


@app.route("/cycles", methods=["GET"])
def get_cycles():
    battery_id = request.args.get("battery_id", type=str)
    try:
        session = Session()
        query = session.query(Battery)

        if battery_id:
            battery = query.filter_by(battery_id=battery_id).one_or_none()

            if battery is None:
                logger.error(f"error: Could not find the battery with ID: {battery_id}, status code: 404")
                return jsonify({"error": f"Could not find the battery with ID: {battery_id}"}), 404

            return jsonify({
                "battery_id": battery_id,
                "cycles": battery.cycles
                }), 200
        else:
            batteries = query.all()
            return jsonify([
                {"battery_id": b.battery_id, "cycles": b.cycles} for b in batteries
                ])

    except Exception as e:
        logger.error(f"Internal Server Error: {e}, status code: 500")
        return jsonify({"Internal Server Error": str(e)}), 500

    finally:
        session.close()
