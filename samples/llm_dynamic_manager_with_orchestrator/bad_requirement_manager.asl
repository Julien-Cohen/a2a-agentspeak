!start.

sleep_time(10).

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+spec(S)[source(F)] <-
    +from(F) ;
    .print("I received from", F, "the specification to manage:", S).

+!build : spec(S) <-
    !reply_with_failure.

+!build : not spec(_) & from(F) <-
    .print("Error : received build request from", F, "but did not receive specification.") ;
    !reply_with_failure.

+!build[source(F)] : not spec(_) <-
    .print("Error : received build request from", F, "but did not receive specification.") ;
    +from(F) ;
    !reply_with_failure.

+from(F) <-
    .print("Reply-to:", F).

+!reply_with_failure : from(F) <-
    .print("Reporting failure to", F) ;
    .my_name(N) ;
    .send(F, tell, failure).

+!reply_with_failure : not from(_) <-
    .print("Failed to report failure.") ;
    .fail.
