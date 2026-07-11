      *================================================================*
      * PROGRAM: PAYMENT-PROCESSING
      * PURPOSE: Processes customer payments, calculates late fees,
      *          applies discounts, and updates the payment ledger.
      * THIS IS SAMPLE DATA for testing the agent network.
      *================================================================*
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYMENT-PROCESSING.
       AUTHOR. LEGACY-TEAM.
       DATE-WRITTEN. 1998-03-15.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT PAYMENT-FILE ASSIGN TO 'PAYFILE.DAT'
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.

           SELECT REPORT-FILE ASSIGN TO 'PAYRPT.DAT'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD PAYMENT-FILE.
       01 PAYMENT-RECORD.
           05 PR-CUSTOMER-ID      PIC X(10).
           05 PR-INVOICE-NUMBER   PIC 9(8).
           05 PR-AMOUNT-DUE       PIC 9(7)V99.
           05 PR-AMOUNT-PAID      PIC 9(7)V99.
           05 PR-DUE-DATE         PIC 9(8).
           05 PR-PAYMENT-DATE     PIC 9(8).

       WORKING-STORAGE SECTION.
       01 WS-FILE-STATUS          PIC XX.
       01 WS-EOF-FLAG             PIC X VALUE 'N'.
       01 WS-DAYS-OVERDUE         PIC 9(4) VALUE ZEROS.
       01 WS-LATE-FEE             PIC 9(7)V99 VALUE ZEROS.
       01 WS-LATE-FEE-RATE        PIC 9V99 VALUE 0.05.
       01 WS-DISCOUNT-AMOUNT      PIC 9(7)V99 VALUE ZEROS.
       01 WS-EARLY-PAY-RATE       PIC 9V99 VALUE 0.02.
       01 WS-NET-AMOUNT           PIC 9(7)V99 VALUE ZEROS.
       01 WS-TOTAL-PROCESSED      PIC 9(6) VALUE ZEROS.
       01 WS-TOTAL-LATE-FEES      PIC 9(9)V99 VALUE ZEROS.
       01 WS-PAYMENT-THRESHOLD    PIC 9(7)V99 VALUE 10000.00.
       01 WS-HIGH-VALUE-FLAG      PIC X VALUE 'N'.

       PROCEDURE DIVISION.
       MAIN-PROCESS.
           OPEN INPUT PAYMENT-FILE
           OPEN OUTPUT REPORT-FILE
           PERFORM READ-PAYMENT
           PERFORM PROCESS-PAYMENTS UNTIL WS-EOF-FLAG = 'Y'
           PERFORM GENERATE-SUMMARY
           CLOSE PAYMENT-FILE
           CLOSE REPORT-FILE
           STOP RUN.

       READ-PAYMENT.
           READ PAYMENT-FILE INTO PAYMENT-RECORD
               AT END MOVE 'Y' TO WS-EOF-FLAG
           END-READ.

       PROCESS-PAYMENTS.
           PERFORM CALCULATE-DAYS-OVERDUE
           PERFORM CHECK-HIGH-VALUE
           IF WS-DAYS-OVERDUE > 30
               PERFORM CALCULATE-LATE-FEE
           ELSE
               IF WS-DAYS-OVERDUE < 0
                   PERFORM CALCULATE-EARLY-DISCOUNT
               ELSE
                   MOVE PR-AMOUNT-DUE TO WS-NET-AMOUNT
               END-IF
           END-IF
           PERFORM UPDATE-LEDGER
           ADD 1 TO WS-TOTAL-PROCESSED
           PERFORM READ-PAYMENT.

       CALCULATE-DAYS-OVERDUE.
           COMPUTE WS-DAYS-OVERDUE =
               PR-PAYMENT-DATE - PR-DUE-DATE.

       CHECK-HIGH-VALUE.
           IF PR-AMOUNT-DUE > WS-PAYMENT-THRESHOLD
               MOVE 'Y' TO WS-HIGH-VALUE-FLAG
               CALL 'HIGHVAL01' USING PR-CUSTOMER-ID
                                      PR-AMOUNT-DUE
           ELSE
               MOVE 'N' TO WS-HIGH-VALUE-FLAG
           END-IF.

       CALCULATE-LATE-FEE.
           COMPUTE WS-LATE-FEE =
               PR-AMOUNT-DUE * WS-LATE-FEE-RATE
           COMPUTE WS-NET-AMOUNT =
               PR-AMOUNT-DUE + WS-LATE-FEE
           ADD WS-LATE-FEE TO WS-TOTAL-LATE-FEES
           CALL 'NOTIF01' USING PR-CUSTOMER-ID
                                 WS-LATE-FEE.

       CALCULATE-EARLY-DISCOUNT.
           COMPUTE WS-DISCOUNT-AMOUNT =
               PR-AMOUNT-DUE * WS-EARLY-PAY-RATE
           COMPUTE WS-NET-AMOUNT =
               PR-AMOUNT-DUE - WS-DISCOUNT-AMOUNT.

       UPDATE-LEDGER.
           CALL 'LEDGER01' USING PR-CUSTOMER-ID
                                  PR-INVOICE-NUMBER
                                  WS-NET-AMOUNT
                                  WS-HIGH-VALUE-FLAG.

       GENERATE-SUMMARY.
           DISPLAY 'TOTAL PAYMENTS PROCESSED: ' WS-TOTAL-PROCESSED
           DISPLAY 'TOTAL LATE FEES COLLECTED: ' WS-TOTAL-LATE-FEES.
