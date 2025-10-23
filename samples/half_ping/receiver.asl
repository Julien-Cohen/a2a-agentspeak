!start.

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+!ping[source(S)] <-
    .print("Received a ping from", S);
    .send(S, tell, pong).

