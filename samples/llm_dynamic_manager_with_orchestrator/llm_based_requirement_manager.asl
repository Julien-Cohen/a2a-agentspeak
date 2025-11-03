!start.

sleep_time(10). # milliseconds

+!start <-
    .my_name(N) ;
    .print("Hello from", N).

+spec(S)[source(F)] <-
    +from(F) ;
    .print("I received the specification to manage:", S).

+!build : spec(S) & not req(_) <-
    .print("(Init) No list of requirements found, creating an empty list.");
    +req([]) ;
    !build.

+!build : spec(S) & req(L) <-
    .print("Consulting LLM for evaluation.") ;
     .prompt_completeness(spec(S), req(L), RES) ;
    .print("Received", RES);
    if(RES == failure) { !reply_with_failure }
    else {
        ?sleep_time(T) ;
        .print("Sleeping" , T, "ms.") ;
        .wait(T) ;
        +completeness(RES)
    }.

+!build : from(F) <-
   .print ("Unexpected case (report failure).") ;
   !reply_with_failure(F).

+!build : from(F) & not spec(_) <-
   .print ("Unexpected case : no specification received (report failure).") ;
   !reply_with_failure(F).


+!build[source(F)]: not spec(_) <-
    .print ("Unexpected case : no specification received before build request from", F).

+!build <-
    .print ("Unexpected case.").

+completeness(complete) : req(L) & from(F) <-
    .print("List of requirements complete:", L) ;
    .print("Sent to", F);
    .send(F, tell, reply(L)).

+completeness(incomplete) : spec(S) & req(L) <-
    .print("Consulting LLM for generation.") ;
    .prompt_generate(spec(S), req(L), RES) ;
    if(RES == failure) { !reply_with_failure }
    else {
        -req(L) ;
        +req([RES|L]) ;
         ?sleep_time(T) ;
        .print("Sleeping" , T, "ms.") ;
        .wait(T) ;
        !build
    }.


+completeness(Other) <-
    .print ("other:", Other).

+req(L) <-
    .print("Status of requirements:", L).

+from(F) <-
    .print("Reply-to:", F).


+!reply_with_failure : from(F) <-
    .my_name(N) ;
    .send(F, tell, failure(N)).
