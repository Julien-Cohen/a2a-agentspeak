!start.

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+!ping[source(X)] <-
    .print("I received a ping request from", X);
    .send(X, tell, pong).

+secret(X) <-
    .print("New belief : the secret is ", X).
