/github-copilot-starter

# Task
setup a Python project for github copilot called called "autotune-app". 

# Context
The project will use an exisiting `autotune`  tool to generate AAPS profiles based on history stored in nightscout. It is used to load an existing nightscout profile, load historyical data from nightscout, run autotune to get a suggestion on a new profile, and sync that profile to nightscout. Eventually it will be a streamlit app with which the user can run it. This app uses jobs sent to a Prefect server, which contains a flow to run autotune. This flow consists of tasks like load data, run autotune, and sync profile. All parts will be tested with unit tests and integration tests. Development is done using Dev containers. 


# References
- [Android AAPS](https://androidaps.readthedocs.io/en/latest/index.html)
- [Autotune tool](https://github.com/openaps/oref0/blob/master/bin/oref0-autotune.py)
- Existing project which has a dockerfile to run autotune, will use it to base on this. But build own python fnctions with prefect and streamlit app: [github repo](https://github.com/houthacker/nightscout-autotune)

