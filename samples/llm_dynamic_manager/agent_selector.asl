!start.

sleep_time(10).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+!register(A) <-
    +available_agent(A) ;
    .print("All registered agents:");
    for (available_agent(X)) { .print(X) }.


+from(F) <-
    .print("Reply-to:", F).


+!reply_with_failure : from(F) <-
    .my_name(N) ;
    .send(F, tell, failure(N)).
