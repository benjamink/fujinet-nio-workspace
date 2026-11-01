.export _traffic_dli, _traffic_dli_count
.include "atari.inc"
.bss
_traffic_dli_count: .res 1
.code
.proc _traffic_dli
        pha
        txa
        pha
        lda _traffic_dli_count
        cmp #$ff
        beq :+
        inc _traffic_dli_count
:       ldx #25
:       dex
        bne :-
        pla
        tax
        pla
        rti
.endproc
