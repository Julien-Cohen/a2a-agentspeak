!start.

pos(0).

+!start <-
    .my_name(N) ;
    .print("hello from", N).

+!do_move : pos(X) <-
    .print("I received a move request.") ;
    -+pos(X+1) ;
    ?pos(Y) ;
    .print("I moved at pos", Y).

+!move_by(D) : pos(X) <-
    .print("I received a move-by request.") ;
    -+pos(X+D) ;
    ?pos(Y) ;
    .print("I moved at pos", Y).

+!do_jump <-
    ?pos(P);
    .print("I received a jump request, while I am at pos", P);
    jump.