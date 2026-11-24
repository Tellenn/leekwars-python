# log_lib.py
# Personal-fight-log helpers. Debug.log() writes to YOUR private log,
# readable in the end-of-fight report (max ~500k chars per fight).

ENABLED = True  # set False to silence every log of the AI


def log(message):
    if ENABLED:
        Debug.log("[AI] " + str(message))
