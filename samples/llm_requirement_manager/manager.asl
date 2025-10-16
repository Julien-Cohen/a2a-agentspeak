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

+!build : spec(S) & req(L) <-
    .print("List of requirements found. Going to ask for completeness.", L) ;
    .prompt_completeness(spec(S), req(L), RES) ;
    .print("Received", RES);
    +completeness(RES).

+completeness(complete) : req(L) & from(F) <-
    .print("List of requirements complete:", L) ;
    .print("Sent to", F);
    .send(F, tell, req(L)).

+completeness(incomplete) : spec(S) & req(L) <-
    .print("List of requirements not complete") ;
    .prompt_generate(spec(S), req(L), RES) ;
    -req(L) ;
    +req([RES|L]) ;
    !build.

+completeness(Other) <-
    .print ("other:", Other).

+req(L) <-
    .print("Status of requirements:", L).

+from(F) <-
    .print("Reply-to:", F).
