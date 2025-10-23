!start.

sleep_time(15000).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+spec(S)[source(F)] <-
    +from(F) ;
    .print("I received the specification to manage:", S).

+!build : spec(S) & not req(_) <-
    .print("No list of requirements found, creating an empty list.");
    +req([]) ;
    !build.

+!build : spec(S) & req(L) <-
    .print("Consulting LLM") ;
     .prompt_completeness(spec(S), req(L), RES) ;
    .print("Received", RES);
    if(RES == failure) { !reply_with_failure }
    else {
        ?sleep_time(T) ;
        .print("Sleeping" , T, "ms.") ;
        .wait(T) ;
        +completeness(RES)
    }.


+completeness(complete) : req(L) & from(F) <-
    .print("List of requirements complete:", L) ;
    .print("Sent to", F);
    .send(F, tell, req(L)).

+completeness(incomplete) : spec(S) & req(L) <-
    .print("Consulting LLM") ;
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
    .send(F, tell, failure).
