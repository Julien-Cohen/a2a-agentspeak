!start.
reply(-1).

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+ready:
    .print("I received the ready signal").


+!ping : ready <-
    .print("I have been invoked by an achievement (ready)") ;
    ?reply(X) ;
    -reply(X) ;
    +reply(42) ;
    !check.

+!ping <-
    .print("I have been invoked by an achievement (not ready)") ;
    ?reply(X) ;
    -reply(X) ;
    +reply(0) ;
    !check.

+!check : reply(X) <- .print ("Current reply is", X).