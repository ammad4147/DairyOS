# Reporting backend linkage validation gate

This branch must not merge until Python, security, forensic-source, Windows desktop, and Windows installer checks required by repository policy are green for the branch/PR head. Backend linkage tests additionally guard read-only source behavior, date normalization, Milk NULL-versus-zero semantics, Finance VOID semantics, owner cash-movement classification, canonical herd labels, and the three Milk sessions.
