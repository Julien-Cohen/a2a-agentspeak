!start.

sleep_time(10).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+!register(A) <-
    +available_agent(A) ;
    !print_available_agents.

+has_requirement_manager_interface(A) <-
    .print("I have been told that", A, "has convenient interface.").

+!print_available_agents <-
    .print("All registered agents:");
    for (available_agent(X)) { .print(X) }.

+selected(A) : available_agent(A) <-
    .print("Selecting agent", A).

+selected(A) : not available_agent(A) <-
    .print("Warning : selected an agent which is not available.").

+from(F) <-
    .print("Reply-to:", F).


+!reply_with_failure : from(F) <-
    .my_name(N) ;
    .send(F, tell, failure(N)).

+failure(A) <-
    -failure(A) ;
    +failure.

+failed(A) : available_agent(A) <-
    .print("Received: failure from", A);
    .print("Removing", A, "from registered agents.");
    -available_agent(A) ;
    !print_available_agents ;
    .print("Trying with another agent.");
    !select_another ;
    !build.

+!select_another : available_agent(A) & has_requirement_manager_interface(A) <-
    +selected(A).

+!select_another <-
    .print("No agent available for this task.").

+failed(A) : not available_agent(A) <-
    .print("Received an information about", A, "but that agent was not registered").

+failure : selected(A) <-
    -failure ;
    +failed(A).

+spec(S) <-
    .print("Specification received.").

+!build : spec(S) & selected(A) & available_agent(A)<-
    .print("received the order to start the job");
    .send(A, tell, spec(S)) ;
    .print("(spec sent)") ;
    .send(A, achieve, build) ;
    .print("(build sent)").

+!build : not spec(_) <-
    .print("Warning: Cannot process because of missing spec.").

+!build : not selected(_) <-
    .print("Warning: Cannot process because no agent has been selected.").

+!build : not available_agent(_) <-
    .print("Warning: Cannot process because no agent is available.").

+!build : selected(A) & available_agent(B) <-
    .print("Warning: Cannot process (mismatch between selected agent", A, "and available agents).").


+reply(L) <-
    .print ("Answer received from requirement manager.") ;
    .print("Answer is:", L).

+reply <-
    .print ("Bad answer received from requirement manager.").