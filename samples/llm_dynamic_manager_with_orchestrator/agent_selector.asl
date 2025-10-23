!start.

sleep_time(10).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+!register(A) <-
    +available_agent(A) ;
    !print_available_agents.

+!print_available_agents <-
    .print("All registered agents:");
    for (available_agent(X)) { .print(X) }.

+selected(A) : available_agent(A) <-
    .print("Received: Selected agent is", A).

+selected(A) : not available_agent(A) <-
    .print("Warning : selected an agent which is not available.").

+from(F) <-
    .print("Reply-to:", F).


+!reply_with_failure : from(F) <-
    .my_name(N) ;
    .send(F, tell, failure(N)).

+failed(A) : available_agent(A) <-
    .print("Received: failure from", A);
    .print("Removing", A, "from registered agents.");
    -available_agent(A) ;
    !print_available_agents.

+failed(A) : not available_agent(A) <-
    .print("Received an information about", A, "but that agent was not registered").