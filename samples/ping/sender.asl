!start.

secret(42).

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+!do_ping(DEST) <-
    .print("I received a ping request with destination", DEST);
    .send_str(DEST, tell, sender_alive);
    .wait(1000);
    .print("Sent.").


+!share_secret(DEST) : secret(X) <-
    .print("I received a request tp share my secret with", DEST);
    .send_str(DEST, tell, secret(X)).

