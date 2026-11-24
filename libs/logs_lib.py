# log_lib.py
# Personal-fight-log helpers. Debug.log() writes to YOUR private log,
# readable in the end-of-fight report (max ~500k chars per fight).
#
# LOG POLICY (see AGENTS.md) :
#   - the "once" blocks (identity of the AI, own stats, equipment) are
#     written ONCE per fight: the fight report would otherwise be flooded
#     with the same header every turn;
#   - the state of the fight and the profitability report are written EVERY
#     turn, in a compact form (one short line per item).

ENABLED = True  # set False to silence every log of the AI

#: Name of the AI as displayed in the report (the entry file's name on the
#: site). Keep it in sync with the entry file name.
AI_NAME = "Kepo_solo"

#: Keys already written by log_once (module state, persists across turns).
_LOGGED_ONCE = set()

#: Turn number seen during the last write (used to detect a new fight).
_LAST_TURN = None


def log(message):
    if ENABLED:
        Debug.log("[AI] " + str(message))


def _fight_turn():
    # Current turn number, None if the fight context is not available.
    try:
        return Fight.turn
    except NameError:
        return None


def log_once(key, message):
    # Writes the message the first time it is called with this key.
    # Used for the blocks that are identical from one turn to the next.
    #
    # The blocks are written again when a new fight starts (the turn counter
    # goes backwards), so each fight report gets its own header.
    global _LAST_TURN
    if not ENABLED:
        return
    turn = _fight_turn()
    if turn is not None:
        if _LAST_TURN is not None and turn < _LAST_TURN:
            _LOGGED_ONCE.clear()
        _LAST_TURN = turn
    if key in _LOGGED_ONCE:
        return
    _LOGGED_ONCE.add(key)
    Debug.log("[AI] " + str(message))


def reset():
    # Forgets the blocks already written: call it at the start of a new
    # fight (the site re-evaluates the module, tests call it explicitly).
    global _LAST_TURN
    _LOGGED_ONCE.clear()
    _LAST_TURN = None
