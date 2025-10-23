!start.

sleep_time(10).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+spec(S)[source(F)] <-
    +from(F) ;
    .print("I received from", F, "the specification to manage:", S).

+!build : spec(S) & not req(_) <-
    .print("No list of requirements found, creating an empty list.");
    +req([]) ;
    !build.

+!build : spec(S) & req(L) <-
    !reply_with_failure.



+from(F) <-
    .print("Reply-to:", F).


+!reply_with_failure : from(F) <-
    .my_name(N) ;
    .send(F, tell, failure).
