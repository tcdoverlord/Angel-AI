def run(brain):
    print("╭──────────────────────────────────────────────╮\n│ ANGEL AI V2                                  │\n│ Local Ollama • deterministic tools • modular │\n╰──────────────────────────────────────────────╯")
    print("Type /help for commands. Type /exit to quit.\n")
    while True:
        try:t=input("You > ").strip()
        except (EOFError,KeyboardInterrupt): print(); break
        if not t:continue
        if t=="/exit":break
        if t=="/help":print("/help /status /model /time /weather [location] /exit");continue
        if t=="/status":print(f"Ollama: {brain.client.base_url}\nModel: {brain.model}\nLocation: {brain.location}");continue
        if t=="/model":print(brain.model);continue
        if t=="/time":print(brain.respond("what date and time is it"));continue
        if t.startswith("/weather"): print(brain.respond("weather in "+(t[8:].strip() or brain.location)));continue
        print("\nAngel > "+brain.respond(t)+"\n")
