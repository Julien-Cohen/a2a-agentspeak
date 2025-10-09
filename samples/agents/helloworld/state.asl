!start.
secret(-1).

+!start <-
    .my_name(N) ;
    .print("Hello from", N) ;
    !test.

+ready[source(S)]:
    .print("I received the ready signal from", S).


+!ping : ready <-
    .print("I have been invoked by an achievement (while ready)") ;
    ?secret(X) ;
    -secret(X) ;
    +secret(42).

+!ping <-
    .print("I have been invoked by an achievement (while not ready)") ;
    ?secret(X) ;
    -secret(X) ;
    +secret(0).

+!test <- .print_float(1) .
