      *================================================================*
      * PROGRAM: INVENTORY-CHECK
      * PURPOSE: Checks stock levels, triggers reorder when inventory
      *          falls below threshold, and logs stock movements.
      * THIS IS SAMPLE DATA for testing the agent network.
      *================================================================*
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVENTORY-CHECK.
       AUTHOR. LEGACY-TEAM.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT INVENTORY-FILE ASSIGN TO 'INVFILE.DAT'
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS INV-PRODUCT-ID
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD INVENTORY-FILE.
       01 INVENTORY-RECORD.
           05 INV-PRODUCT-ID      PIC X(8).
           05 INV-PRODUCT-NAME    PIC X(30).
           05 INV-QUANTITY         PIC 9(5).
           05 INV-REORDER-LEVEL   PIC 9(5).
           05 INV-REORDER-QTY     PIC 9(5).
           05 INV-UNIT-PRICE      PIC 9(5)V99.
           05 INV-WAREHOUSE-CODE  PIC X(4).

       WORKING-STORAGE SECTION.
       01 WS-FILE-STATUS          PIC XX.
       01 WS-EOF-FLAG             PIC X VALUE 'N'.
       01 WS-REORDER-COUNT        PIC 9(4) VALUE ZEROS.
       01 WS-CRITICAL-FLAG        PIC X VALUE 'N'.
       01 WS-CRITICAL-THRESHOLD   PIC 9(3) VALUE 10.
       01 WS-TOTAL-VALUE          PIC 9(9)V99 VALUE ZEROS.
       01 WS-ITEM-VALUE           PIC 9(9)V99 VALUE ZEROS.

       PROCEDURE DIVISION.
       MAIN-PROCESS.
           OPEN I-O INVENTORY-FILE
           PERFORM READ-NEXT-ITEM
           PERFORM CHECK-INVENTORY UNTIL WS-EOF-FLAG = 'Y'
           PERFORM DISPLAY-SUMMARY
           CLOSE INVENTORY-FILE
           STOP RUN.

       READ-NEXT-ITEM.
           READ INVENTORY-FILE NEXT INTO INVENTORY-RECORD
               AT END MOVE 'Y' TO WS-EOF-FLAG
           END-READ.

       CHECK-INVENTORY.
           PERFORM CALCULATE-ITEM-VALUE
           IF INV-QUANTITY < INV-REORDER-LEVEL
               PERFORM TRIGGER-REORDER
           END-IF
           IF INV-QUANTITY < WS-CRITICAL-THRESHOLD
               MOVE 'Y' TO WS-CRITICAL-FLAG
               CALL 'ALERT01' USING INV-PRODUCT-ID
                                     INV-QUANTITY
           END-IF
           PERFORM READ-NEXT-ITEM.

       CALCULATE-ITEM-VALUE.
           COMPUTE WS-ITEM-VALUE =
               INV-QUANTITY * INV-UNIT-PRICE
           ADD WS-ITEM-VALUE TO WS-TOTAL-VALUE.

       TRIGGER-REORDER.
           ADD 1 TO WS-REORDER-COUNT
           CALL 'REORDER01' USING INV-PRODUCT-ID
                                   INV-REORDER-QTY
                                   INV-WAREHOUSE-CODE.

       DISPLAY-SUMMARY.
           DISPLAY 'ITEMS NEEDING REORDER: ' WS-REORDER-COUNT
           DISPLAY 'TOTAL INVENTORY VALUE: ' WS-TOTAL-VALUE.
