# Battery-Simulator

This is a simple battery simulator that can be used to do the following:

- Create a new instance of the battery.
- Charge or discharge that battery using a power setpoint and duration. Positive power means the battery will be charged and negative power will discharge the battery. Duration is in minutes to keep it simple.
- Can get the current state of a single battery
- Can get all the battery details
- Delete an instance of the battery
- Can get soc of all the batteries and also for a single battery, given the battery id as query param.
- Can get battery cycle count of all the batteries and also for a single battery, given the battery id as query param.

The application can be used by running the `python run.py` command or by building the docker image `docker build -t <image-name> .` and running it with `docker run -p 8080:8080 <image-name>`