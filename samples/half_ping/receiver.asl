!start.

+!start <-
    .print("hello from receiver").

+!ping[source(S)] <-
    .print("Received a ping from", S);
    .send(S, tell, "pong").

