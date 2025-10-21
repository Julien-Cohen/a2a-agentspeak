!start.

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

+!build : spec(S) & req(L) & .print("Consulting LLM") & .prompt_completeness(spec(S), req(L), RES) <-
    .print("Received", RES);
    .print("Sleeping 10 seconds.") ;
    .wait(10000) ;
    .print("wake up") ;
    +completeness(RES).

+!build : .print("backup") & spec(S) & req(L) <-
    .print("Prompt failed.").

+completeness(complete) : req(L) & from(F) <-
    .print("List of requirements complete:", L) ;
    .print("Sent to", F);
    .send(F, tell, req(L)).

+completeness(incomplete) : spec(S) & req(L) & .print("Consulting LLM") & .prompt_generate(spec(S), req(L), RES) <-
    -req(L) ;
    +req([RES|L]) ;
    .print("Sleeping 10 seconds.") ;
    .wait(10000) ;
    .print("wake up") ;
    !build.

+completeness(incomplete) : spec(S) & req(L) <-
    .print("Generation by LLM failed.").

+completeness(Other) <-
    .print ("other:", Other).

+req(L) <-
    .print("Status of requirements:", L).

+from(F) <-
    .print("Reply-to:", F).
