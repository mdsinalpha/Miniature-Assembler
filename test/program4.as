addi 1,0,n # n 
addi 2,0,1 # a = 1
addi 3,0,1 # b = 1
addi 4,0,2 # i = 2
Loop slt 5,4,1 # i < n : $5 = 1 , i>= n : $5 = 0
beq 5,0,Exit
add 6,2,3 # c = a + b 
addi 4,4,1 # i++
add 2,0,3 # a = b
add 3,0,6 # b = c
j Loop
Exit sw 3,0,0
halt
n .fill 16