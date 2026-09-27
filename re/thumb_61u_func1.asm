
/tmp/thumb_61u_func1.bin:     file format binary


Disassembly of section .data:

1078c8d0 <.data>:
1078c8d0:	b5f0      	push	{r4, r5, r6, r7, lr}
1078c8d2:	b083      	sub	sp, #12
1078c8d4:	4606      	mov	r6, r0
1078c8d6:	2800      	cmp	r0, #0
1078c8d8:	d107      	bne.n	0x1078c8ea
1078c8da:	2200      	movs	r2, #0
1078c8dc:	2100      	movs	r1, #0
1078c8de:	48ba      	ldr	r0, [pc, #744]	@ (0x1078cbc8)
1078c8e0:	2300      	movs	r3, #0
1078c8e2:	f0b2 eca4 	blx	0x1083f22c
1078c8e6:	b003      	add	sp, #12
1078c8e8:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c8ea:	2029      	movs	r0, #41	@ 0x29
1078c8ec:	0180      	lsls	r0, r0, #6
1078c8ee:	1834      	adds	r4, r6, r0
1078c8f0:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c8f2:	2800      	cmp	r0, #0
1078c8f4:	d107      	bne.n	0x1078c906
1078c8f6:	2200      	movs	r2, #0
1078c8f8:	2100      	movs	r1, #0
1078c8fa:	48b4      	ldr	r0, [pc, #720]	@ (0x1078cbcc)
1078c8fc:	2300      	movs	r3, #0
1078c8fe:	f0b2 ec96 	blx	0x1083f22c
1078c902:	b003      	add	sp, #12
1078c904:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c906:	6800      	ldr	r0, [r0, #0]
1078c908:	2700      	movs	r7, #0
1078c90a:	2800      	cmp	r0, #0
1078c90c:	d00d      	beq.n	0x1078c92a
1078c90e:	2200      	movs	r2, #0
1078c910:	2100      	movs	r1, #0
1078c912:	48af      	ldr	r0, [pc, #700]	@ (0x1078cbd0)
1078c914:	2300      	movs	r3, #0
1078c916:	f0b2 ec8a 	blx	0x1083f22c
1078c91a:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c91c:	2800      	cmp	r0, #0
1078c91e:	d0f0      	beq.n	0x1078c902
1078c920:	f0b2 ecd6 	blx	0x1083f2d0
1078c924:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078c926:	b003      	add	sp, #12
1078c928:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c92a:	2008      	movs	r0, #8
1078c92c:	f0b2 ecc8 	blx	0x1083f2c0
1078c930:	4605      	mov	r5, r0
1078c932:	2d00      	cmp	r5, #0
1078c934:	d10d      	bne.n	0x1078c952
1078c936:	2200      	movs	r2, #0
1078c938:	2100      	movs	r1, #0
1078c93a:	48a6      	ldr	r0, [pc, #664]	@ (0x1078cbd4)
1078c93c:	2300      	movs	r3, #0
1078c93e:	f0b2 ec76 	blx	0x1083f22c
1078c942:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c944:	2800      	cmp	r0, #0
1078c946:	d0ee      	beq.n	0x1078c926
1078c948:	f0b2 ecc2 	blx	0x1083f2d0
1078c94c:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078c94e:	b003      	add	sp, #12
1078c950:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c952:	2004      	movs	r0, #4
1078c954:	f0b2 ecb4 	blx	0x1083f2c0
1078c958:	6028      	str	r0, [r5, #0]
1078c95a:	606f      	str	r7, [r5, #4]
1078c95c:	2800      	cmp	r0, #0
1078c95e:	d110      	bne.n	0x1078c982
1078c960:	2200      	movs	r2, #0
1078c962:	2100      	movs	r1, #0
1078c964:	489c      	ldr	r0, [pc, #624]	@ (0x1078cbd8)
1078c966:	2300      	movs	r3, #0
1078c968:	f0b2 ec60 	blx	0x1083f22c
1078c96c:	4628      	mov	r0, r5
1078c96e:	f0b2 ecb0 	blx	0x1083f2d0
1078c972:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c974:	2800      	cmp	r0, #0
1078c976:	d0ea      	beq.n	0x1078c94e
1078c978:	f0b2 ecaa 	blx	0x1083f2d0
1078c97c:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078c97e:	b003      	add	sp, #12
1078c980:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c982:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c984:	68c1      	ldr	r1, [r0, #12]
1078c986:	6b30      	ldr	r0, [r6, #48]	@ 0x30
1078c988:	6802      	ldr	r2, [r0, #0]
1078c98a:	3280      	adds	r2, #128	@ 0x80
1078c98c:	6813      	ldr	r3, [r2, #0]
1078c98e:	462a      	mov	r2, r5
1078c990:	4798      	blx	r3
1078c992:	2800      	cmp	r0, #0
1078c994:	d1f3      	bne.n	0x1078c97e
1078c996:	6828      	ldr	r0, [r5, #0]
1078c998:	2800      	cmp	r0, #0
1078c99a:	d002      	beq.n	0x1078c9a2
1078c99c:	6800      	ldr	r0, [r0, #0]
1078c99e:	2800      	cmp	r0, #0
1078c9a0:	d117      	bne.n	0x1078c9d2
1078c9a2:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c9a4:	2200      	movs	r2, #0
1078c9a6:	2300      	movs	r3, #0
1078c9a8:	8901      	ldrh	r1, [r0, #8]
1078c9aa:	488c      	ldr	r0, [pc, #560]	@ (0x1078cbdc)
1078c9ac:	f0b2 ec3e 	blx	0x1083f22c
1078c9b0:	6828      	ldr	r0, [r5, #0]
1078c9b2:	2800      	cmp	r0, #0
1078c9b4:	d002      	beq.n	0x1078c9bc
1078c9b6:	f0b2 ec8c 	blx	0x1083f2d0
1078c9ba:	602f      	str	r7, [r5, #0]
1078c9bc:	4628      	mov	r0, r5
1078c9be:	f0b2 ec88 	blx	0x1083f2d0
1078c9c2:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078c9c4:	2800      	cmp	r0, #0
1078c9c6:	d0da      	beq.n	0x1078c97e
1078c9c8:	f0b2 ec82 	blx	0x1083f2d0
1078c9cc:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078c9ce:	b003      	add	sp, #12
1078c9d0:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078c9d2:	f0b2 ec76 	blx	0x1083f2c0
1078c9d6:	6068      	str	r0, [r5, #4]
1078c9d8:	2800      	cmp	r0, #0
1078c9da:	d11c      	bne.n	0x1078ca16
1078c9dc:	2200      	movs	r2, #0
1078c9de:	2100      	movs	r1, #0
1078c9e0:	487f      	ldr	r0, [pc, #508]	@ (0x1078cbe0)
1078c9e2:	2300      	movs	r3, #0
1078c9e4:	f0b2 ec22 	blx	0x1083f22c
1078c9e8:	6828      	ldr	r0, [r5, #0]
1078c9ea:	2800      	cmp	r0, #0
1078c9ec:	d002      	beq.n	0x1078c9f4
1078c9ee:	f0b2 ec70 	blx	0x1083f2d0
1078c9f2:	602f      	str	r7, [r5, #0]
1078c9f4:	6868      	ldr	r0, [r5, #4]
1078c9f6:	2800      	cmp	r0, #0
1078c9f8:	d002      	beq.n	0x1078ca00
1078c9fa:	f0b2 ec6a 	blx	0x1083f2d0
1078c9fe:	606f      	str	r7, [r5, #4]
1078ca00:	4628      	mov	r0, r5
1078ca02:	f0b2 ec66 	blx	0x1083f2d0
1078ca06:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078ca08:	2800      	cmp	r0, #0
1078ca0a:	d0e0      	beq.n	0x1078c9ce
1078ca0c:	f0b2 ec60 	blx	0x1083f2d0
1078ca10:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078ca12:	b003      	add	sp, #12
1078ca14:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078ca16:	6ae1      	ldr	r1, [r4, #44]	@ 0x2c
1078ca18:	8908      	ldrh	r0, [r1, #8]
1078ca1a:	2897      	cmp	r0, #151	@ 0x97
1078ca1c:	d002      	beq.n	0x1078ca24
1078ca1e:	38ff      	subs	r0, #255	@ 0xff
1078ca20:	380b      	subs	r0, #11
1078ca22:	d12a      	bne.n	0x1078ca7a
1078ca24:	6b30      	ldr	r0, [r6, #48]	@ 0x30
1078ca26:	68c9      	ldr	r1, [r1, #12]
1078ca28:	6802      	ldr	r2, [r0, #0]
1078ca2a:	3280      	adds	r2, #128	@ 0x80
1078ca2c:	6813      	ldr	r3, [r2, #0]
1078ca2e:	462a      	mov	r2, r5
1078ca30:	4798      	blx	r3
1078ca32:	2800      	cmp	r0, #0
1078ca34:	d10b      	bne.n	0x1078ca4e
1078ca36:	496b      	ldr	r1, [pc, #428]	@ (0x1078cbe4)
1078ca38:	9501      	str	r5, [sp, #4]
1078ca3a:	2307      	movs	r3, #7
1078ca3c:	9100      	str	r1, [sp, #0]
1078ca3e:	68f0      	ldr	r0, [r6, #12]
1078ca40:	4a69      	ldr	r2, [pc, #420]	@ (0x1078cbe8)
1078ca42:	6801      	ldr	r1, [r0, #0]
1078ca44:	6d4d      	ldr	r5, [r1, #84]	@ 0x54
1078ca46:	2102      	movs	r1, #2
1078ca48:	031b      	lsls	r3, r3, #12
1078ca4a:	47a8      	blx	r5
1078ca4c:	e01b      	b.n	0x1078ca86
1078ca4e:	2200      	movs	r2, #0
1078ca50:	2100      	movs	r1, #0
1078ca52:	4866      	ldr	r0, [pc, #408]	@ (0x1078cbec)
1078ca54:	2300      	movs	r3, #0
1078ca56:	f0b2 ebea 	blx	0x1083f22c
1078ca5a:	6828      	ldr	r0, [r5, #0]
1078ca5c:	2800      	cmp	r0, #0
1078ca5e:	d002      	beq.n	0x1078ca66
1078ca60:	f0b2 ec36 	blx	0x1083f2d0
1078ca64:	602f      	str	r7, [r5, #0]
1078ca66:	6868      	ldr	r0, [r5, #4]
1078ca68:	2800      	cmp	r0, #0
1078ca6a:	d002      	beq.n	0x1078ca72
1078ca6c:	f0b2 ec30 	blx	0x1083f2d0
1078ca70:	606f      	str	r7, [r5, #4]
1078ca72:	4628      	mov	r0, r5
1078ca74:	f0b2 ec2c 	blx	0x1083f2d0
1078ca78:	e005      	b.n	0x1078ca86
1078ca7a:	2200      	movs	r2, #0
1078ca7c:	2100      	movs	r1, #0
1078ca7e:	485c      	ldr	r0, [pc, #368]	@ (0x1078cbf0)
1078ca80:	2300      	movs	r3, #0
1078ca82:	f0b2 ebd4 	blx	0x1083f22c
1078ca86:	6ae0      	ldr	r0, [r4, #44]	@ 0x2c
1078ca88:	2800      	cmp	r0, #0
1078ca8a:	d0c2      	beq.n	0x1078ca12
1078ca8c:	f0b2 ec20 	blx	0x1083f2d0
1078ca90:	62e7      	str	r7, [r4, #44]	@ 0x2c
1078ca92:	b003      	add	sp, #12
1078ca94:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078ca96:	b5ff      	push	{r0, r1, r2, r3, r4, r5, r6, r7, lr}
1078ca98:	b081      	sub	sp, #4
1078ca9a:	460c      	mov	r4, r1
1078ca9c:	ad0a      	add	r5, sp, #40	@ 0x28
1078ca9e:	cde0      	ldmia	r5, {r5, r6, r7}
1078caa0:	9801      	ldr	r0, [sp, #4]
1078caa2:	2800      	cmp	r0, #0
1078caa4:	d102      	bne.n	0x1078caac
1078caa6:	b005      	add	sp, #20
1078caa8:	2001      	movs	r0, #1
1078caaa:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078caac:	9801      	ldr	r0, [sp, #4]
1078caae:	6b00      	ldr	r0, [r0, #48]	@ 0x30
1078cab0:	6801      	ldr	r1, [r0, #0]
1078cab2:	6aca      	ldr	r2, [r1, #44]	@ 0x2c
1078cab4:	9903      	ldr	r1, [sp, #12]
1078cab6:	4790      	blx	r2
1078cab8:	2800      	cmp	r0, #0
1078caba:	d008      	beq.n	0x1078cace
1078cabc:	2200      	movs	r2, #0
1078cabe:	2100      	movs	r1, #0
1078cac0:	484c      	ldr	r0, [pc, #304]	@ (0x1078cbf4)
1078cac2:	2300      	movs	r3, #0
1078cac4:	f0b2 ebb2 	blx	0x1083f22c
1078cac8:	b005      	add	sp, #20
1078caca:	2001      	movs	r0, #1
1078cacc:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cace:	9803      	ldr	r0, [sp, #12]
1078cad0:	7800      	ldrb	r0, [r0, #0]
1078cad2:	2800      	cmp	r0, #0
1078cad4:	d103      	bne.n	0x1078cade
1078cad6:	9803      	ldr	r0, [sp, #12]
1078cad8:	7880      	ldrb	r0, [r0, #2]
1078cada:	2800      	cmp	r0, #0
1078cadc:	d027      	beq.n	0x1078cb2e
1078cade:	9801      	ldr	r0, [sp, #4]
1078cae0:	9a04      	ldr	r2, [sp, #16]
1078cae2:	6b00      	ldr	r0, [r0, #48]	@ 0x30
1078cae4:	6801      	ldr	r1, [r0, #0]
1078cae6:	6c4b      	ldr	r3, [r1, #68]	@ 0x44
1078cae8:	2101      	movs	r1, #1
1078caea:	4798      	blx	r3
1078caec:	2800      	cmp	r0, #0
1078caee:	d008      	beq.n	0x1078cb02
1078caf0:	2200      	movs	r2, #0
1078caf2:	2100      	movs	r1, #0
1078caf4:	4840      	ldr	r0, [pc, #256]	@ (0x1078cbf8)
1078caf6:	2300      	movs	r3, #0
1078caf8:	f0b2 eb98 	blx	0x1083f22c
1078cafc:	b005      	add	sp, #20
1078cafe:	2001      	movs	r0, #1
1078cb00:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cb02:	9804      	ldr	r0, [sp, #16]
1078cb04:	7800      	ldrb	r0, [r0, #0]
1078cb06:	2800      	cmp	r0, #0
1078cb08:	d11a      	bne.n	0x1078cb40
1078cb0a:	9801      	ldr	r0, [sp, #4]
1078cb0c:	9a04      	ldr	r2, [sp, #16]
1078cb0e:	6b00      	ldr	r0, [r0, #48]	@ 0x30
1078cb10:	6801      	ldr	r1, [r0, #0]
1078cb12:	6c4b      	ldr	r3, [r1, #68]	@ 0x44
1078cb14:	2103      	movs	r1, #3
1078cb16:	4798      	blx	r3
1078cb18:	2800      	cmp	r0, #0
1078cb1a:	d011      	beq.n	0x1078cb40
1078cb1c:	2200      	movs	r2, #0
1078cb1e:	2100      	movs	r1, #0
1078cb20:	4836      	ldr	r0, [pc, #216]	@ (0x1078cbfc)
1078cb22:	2300      	movs	r3, #0
1078cb24:	f0b2 eb82 	blx	0x1083f22c
1078cb28:	b005      	add	sp, #20
1078cb2a:	2001      	movs	r0, #1
1078cb2c:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cb2e:	2200      	movs	r2, #0
1078cb30:	2100      	movs	r1, #0
1078cb32:	4833      	ldr	r0, [pc, #204]	@ (0x1078cc00)
1078cb34:	2300      	movs	r3, #0
1078cb36:	f0b2 eb7a 	blx	0x1083f22c
1078cb3a:	b005      	add	sp, #20
1078cb3c:	2001      	movs	r0, #1
1078cb3e:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cb40:	9804      	ldr	r0, [sp, #16]
1078cb42:	7800      	ldrb	r0, [r0, #0]
1078cb44:	2801      	cmp	r0, #1
1078cb46:	d008      	beq.n	0x1078cb5a
1078cb48:	2802      	cmp	r0, #2
1078cb4a:	d134      	bne.n	0x1078cbb6
1078cb4c:	9803      	ldr	r0, [sp, #12]
1078cb4e:	78c0      	ldrb	r0, [r0, #3]
1078cb50:	0741      	lsls	r1, r0, #29
1078cb52:	d517      	bpl.n	0x1078cb84
1078cb54:	80e6      	strh	r6, [r4, #6]
1078cb56:	802e      	strh	r6, [r5, #0]
1078cb58:	e018      	b.n	0x1078cb8c
1078cb5a:	9803      	ldr	r0, [sp, #12]
1078cb5c:	7840      	ldrb	r0, [r0, #1]
1078cb5e:	0741      	lsls	r1, r0, #29
1078cb60:	d502      	bpl.n	0x1078cb68
1078cb62:	80e6      	strh	r6, [r4, #6]
1078cb64:	802e      	strh	r6, [r5, #0]
1078cb66:	e011      	b.n	0x1078cb8c
1078cb68:	0780      	lsls	r0, r0, #30
1078cb6a:	d502      	bpl.n	0x1078cb72
1078cb6c:	80e7      	strh	r7, [r4, #6]
1078cb6e:	802f      	strh	r7, [r5, #0]
1078cb70:	e00c      	b.n	0x1078cb8c
1078cb72:	2200      	movs	r2, #0
1078cb74:	2100      	movs	r1, #0
1078cb76:	4823      	ldr	r0, [pc, #140]	@ (0x1078cc04)
1078cb78:	2300      	movs	r3, #0
1078cb7a:	f0b2 eb58 	blx	0x1083f22c
1078cb7e:	b005      	add	sp, #20
1078cb80:	2001      	movs	r0, #1
1078cb82:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cb84:	0780      	lsls	r0, r0, #30
1078cb86:	d50d      	bpl.n	0x1078cba4
1078cb88:	80e7      	strh	r7, [r4, #6]
1078cb8a:	802f      	strh	r7, [r5, #0]
1078cb8c:	2000      	movs	r0, #0
1078cb8e:	60a0      	str	r0, [r4, #8]
1078cb90:	60e0      	str	r0, [r4, #12]
1078cb92:	6120      	str	r0, [r4, #16]
1078cb94:	6160      	str	r0, [r4, #20]
1078cb96:	2001      	movs	r0, #1
1078cb98:	80a0      	strh	r0, [r4, #4]
1078cb9a:	2018      	movs	r0, #24
1078cb9c:	6020      	str	r0, [r4, #0]
1078cb9e:	b005      	add	sp, #20
1078cba0:	2000      	movs	r0, #0
1078cba2:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cba4:	2200      	movs	r2, #0
1078cba6:	2100      	movs	r1, #0
1078cba8:	4817      	ldr	r0, [pc, #92]	@ (0x1078cc08)
1078cbaa:	2300      	movs	r3, #0
1078cbac:	f0b2 eb3e 	blx	0x1083f22c
1078cbb0:	b005      	add	sp, #20
1078cbb2:	2001      	movs	r0, #1
1078cbb4:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cbb6:	2200      	movs	r2, #0
1078cbb8:	2100      	movs	r1, #0
1078cbba:	4814      	ldr	r0, [pc, #80]	@ (0x1078cc0c)
1078cbbc:	2300      	movs	r3, #0
1078cbbe:	f0b2 eb36 	blx	0x1083f22c
1078cbc2:	b005      	add	sp, #20
1078cbc4:	2001      	movs	r0, #1
1078cbc6:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cbc8:	3010      	adds	r0, #16
1078cbca:	1133      	asrs	r3, r6, #4
1078cbcc:	3024      	adds	r0, #36	@ 0x24
1078cbce:	1133      	asrs	r3, r6, #4
1078cbd0:	3038      	adds	r0, #56	@ 0x38
1078cbd2:	1133      	asrs	r3, r6, #4
1078cbd4:	304c      	adds	r0, #76	@ 0x4c
1078cbd6:	1133      	asrs	r3, r6, #4
1078cbd8:	3060      	adds	r0, #96	@ 0x60
1078cbda:	1133      	asrs	r3, r6, #4
1078cbdc:	3074      	adds	r0, #116	@ 0x74
1078cbde:	1133      	asrs	r3, r6, #4
1078cbe0:	3088      	adds	r0, #136	@ 0x88
1078cbe2:	1133      	asrs	r3, r6, #4
1078cbe4:	040c      	lsls	r4, r1, #16
1078cbe6:	0000      	movs	r0, r0
1078cbe8:	1a5a      	subs	r2, r3, r1
1078cbea:	0101      	lsls	r1, r0, #4
1078cbec:	309c      	adds	r0, #156	@ 0x9c
1078cbee:	1133      	asrs	r3, r6, #4
1078cbf0:	30b0      	adds	r0, #176	@ 0xb0
1078cbf2:	1133      	asrs	r3, r6, #4
1078cbf4:	3204      	adds	r2, #4
1078cbf6:	1133      	asrs	r3, r6, #4
1078cbf8:	3218      	adds	r2, #24
1078cbfa:	1133      	asrs	r3, r6, #4
1078cbfc:	322c      	adds	r2, #44	@ 0x2c
1078cbfe:	1133      	asrs	r3, r6, #4
1078cc00:	3240      	adds	r2, #64	@ 0x40
1078cc02:	1133      	asrs	r3, r6, #4
1078cc04:	3254      	adds	r2, #84	@ 0x54
1078cc06:	1133      	asrs	r3, r6, #4
1078cc08:	3268      	adds	r2, #104	@ 0x68
1078cc0a:	1133      	asrs	r3, r6, #4
1078cc0c:	327c      	adds	r2, #124	@ 0x7c
1078cc0e:	1133      	asrs	r3, r6, #4
1078cc10:	b5ff      	push	{r0, r1, r2, r3, r4, r5, r6, r7, lr}
1078cc12:	b093      	sub	sp, #76	@ 0x4c
1078cc14:	4611      	mov	r1, r2
1078cc16:	461a      	mov	r2, r3
1078cc18:	4605      	mov	r5, r0
1078cc1a:	9c1c      	ldr	r4, [sp, #112]	@ 0x70
1078cc1c:	9f1d      	ldr	r7, [sp, #116]	@ 0x74
1078cc1e:	2601      	movs	r6, #1
1078cc20:	466b      	mov	r3, sp
1078cc22:	a809      	add	r0, sp, #36	@ 0x24
1078cc24:	c307      	stmia	r3!, {r0, r1, r2}
1078cc26:	ab0a      	add	r3, sp, #40	@ 0x28
1078cc28:	4628      	mov	r0, r5
1078cc2a:	aa0b      	add	r2, sp, #44	@ 0x2c
1078cc2c:	a90d      	add	r1, sp, #52	@ 0x34
1078cc2e:	f7ff ff32 	bl	0x1078ca96
1078cc32:	2800      	cmp	r0, #0
1078cc34:	d002      	beq.n	0x1078cc3c
1078cc36:	b017      	add	sp, #92	@ 0x5c
1078cc38:	2001      	movs	r0, #1
1078cc3a:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cc3c:	2010      	movs	r0, #16
1078cc3e:	f0b2 eb40 	blx	0x1083f2c0
1078cc42:	6020      	str	r0, [r4, #0]
1078cc44:	2800      	cmp	r0, #0
1078cc46:	d102      	bne.n	0x1078cc4e
1078cc48:	b017      	add	sp, #92	@ 0x5c
1078cc4a:	2001      	movs	r0, #1
1078cc4c:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cc4e:	981e      	ldr	r0, [sp, #120]	@ 0x78
1078cc50:	6138      	str	r0, [r7, #16]
1078cc52:	617d      	str	r5, [r7, #20]
1078cc54:	466b      	mov	r3, sp
1078cc56:	22ff      	movs	r2, #255	@ 0xff
1078cc58:	8c99      	ldrh	r1, [r3, #36]	@ 0x24
1078cc5a:	320b      	adds	r2, #11
1078cc5c:	ab0f      	add	r3, sp, #60	@ 0x3c
1078cc5e:	1a88      	subs	r0, r1, r2
1078cc60:	4291      	cmp	r1, r2
1078cc62:	d048      	beq.n	0x1078ccf6
1078cc64:	dc0e      	bgt.n	0x1078cc84
1078cc66:	29a9      	cmp	r1, #169	@ 0xa9
1078cc68:	d045      	beq.n	0x1078ccf6
1078cc6a:	dc06      	bgt.n	0x1078cc7a
1078cc6c:	296d      	cmp	r1, #109	@ 0x6d
1078cc6e:	d042      	beq.n	0x1078ccf6
1078cc70:	2976      	cmp	r1, #118	@ 0x76
1078cc72:	d040      	beq.n	0x1078ccf6
1078cc74:	2997      	cmp	r1, #151	@ 0x97
1078cc76:	d153      	bne.n	0x1078cd20
1078cc78:	e03d      	b.n	0x1078ccf6
1078cc7a:	29cf      	cmp	r1, #207	@ 0xcf
1078cc7c:	d03b      	beq.n	0x1078ccf6
1078cc7e:	29da      	cmp	r1, #218	@ 0xda
1078cc80:	d14e      	bne.n	0x1078cd20
1078cc82:	e038      	b.n	0x1078ccf6
1078cc84:	285c      	cmp	r0, #92	@ 0x5c
1078cc86:	d009      	beq.n	0x1078cc9c
1078cc88:	dc04      	bgt.n	0x1078cc94
1078cc8a:	2819      	cmp	r0, #25
1078cc8c:	d033      	beq.n	0x1078ccf6
1078cc8e:	285b      	cmp	r0, #91	@ 0x5b
1078cc90:	d146      	bne.n	0x1078cd20
1078cc92:	e019      	b.n	0x1078ccc8
1078cc94:	285d      	cmp	r0, #93	@ 0x5d
1078cc96:	d017      	beq.n	0x1078ccc8
1078cc98:	285e      	cmp	r0, #94	@ 0x5e
1078cc9a:	d141      	bne.n	0x1078cd20
1078cc9c:	20ff      	movs	r0, #255	@ 0xff
1078cc9e:	30ef      	adds	r0, #239	@ 0xef
1078cca0:	6821      	ldr	r1, [r4, #0]
1078cca2:	5b40      	ldrh	r0, [r0, r5]
1078cca4:	aa04      	add	r2, sp, #16
1078cca6:	466e      	mov	r6, sp
1078cca8:	1c40      	adds	r0, r0, #1
1078ccaa:	c283      	stmia	r2!, {r0, r1, r7}
1078ccac:	4618      	mov	r0, r3
1078ccae:	c88e      	ldmia	r0!, {r1, r2, r3, r7}
1078ccb0:	c68e      	stmia	r6!, {r1, r2, r3, r7}
1078ccb2:	ab08      	add	r3, sp, #32
1078ccb4:	6b28      	ldr	r0, [r5, #48]	@ 0x30
1078ccb6:	9e0e      	ldr	r6, [sp, #56]	@ 0x38
1078ccb8:	9a0d      	ldr	r2, [sp, #52]	@ 0x34
1078ccba:	6801      	ldr	r1, [r0, #0]
1078ccbc:	6ecd      	ldr	r5, [r1, #108]	@ 0x6c
1078ccbe:	7a19      	ldrb	r1, [r3, #8]
1078ccc0:	4633      	mov	r3, r6
1078ccc2:	47a8      	blx	r5
1078ccc4:	4606      	mov	r6, r0
1078ccc6:	e030      	b.n	0x1078cd2a
1078ccc8:	2011      	movs	r0, #17
1078ccca:	6821      	ldr	r1, [r4, #0]
1078cccc:	0180      	lsls	r0, r0, #6
1078ccce:	1828      	adds	r0, r5, r0
1078ccd0:	aa04      	add	r2, sp, #16
1078ccd2:	8b00      	ldrh	r0, [r0, #24]
1078ccd4:	466e      	mov	r6, sp
1078ccd6:	1c40      	adds	r0, r0, #1
1078ccd8:	c283      	stmia	r2!, {r0, r1, r7}
1078ccda:	4618      	mov	r0, r3
1078ccdc:	c88e      	ldmia	r0!, {r1, r2, r3, r7}
1078ccde:	c68e      	stmia	r6!, {r1, r2, r3, r7}
1078cce0:	ab08      	add	r3, sp, #32
1078cce2:	6b28      	ldr	r0, [r5, #48]	@ 0x30
1078cce4:	9e0e      	ldr	r6, [sp, #56]	@ 0x38
1078cce6:	9a0d      	ldr	r2, [sp, #52]	@ 0x34
1078cce8:	6801      	ldr	r1, [r0, #0]
1078ccea:	6ecd      	ldr	r5, [r1, #108]	@ 0x6c
1078ccec:	7a19      	ldrb	r1, [r3, #8]
1078ccee:	4633      	mov	r3, r6
1078ccf0:	47a8      	blx	r5
1078ccf2:	4606      	mov	r6, r0
1078ccf4:	e019      	b.n	0x1078cd2a
1078ccf6:	6821      	ldr	r1, [r4, #0]
1078ccf8:	9814      	ldr	r0, [sp, #80]	@ 0x50
1078ccfa:	ae05      	add	r6, sp, #20
1078ccfc:	2200      	movs	r2, #0
1078ccfe:	c683      	stmia	r6!, {r0, r1, r7}
1078cd00:	4618      	mov	r0, r3
1078cd02:	9204      	str	r2, [sp, #16]
1078cd04:	c88e      	ldmia	r0!, {r1, r2, r3, r7}
1078cd06:	466e      	mov	r6, sp
1078cd08:	c68e      	stmia	r6!, {r1, r2, r3, r7}
1078cd0a:	ab08      	add	r3, sp, #32
1078cd0c:	6b28      	ldr	r0, [r5, #48]	@ 0x30
1078cd0e:	9e0e      	ldr	r6, [sp, #56]	@ 0x38
1078cd10:	9a0d      	ldr	r2, [sp, #52]	@ 0x34
1078cd12:	6801      	ldr	r1, [r0, #0]
1078cd14:	6f0d      	ldr	r5, [r1, #112]	@ 0x70
1078cd16:	7a19      	ldrb	r1, [r3, #8]
1078cd18:	4633      	mov	r3, r6
1078cd1a:	47a8      	blx	r5
1078cd1c:	4606      	mov	r6, r0
1078cd1e:	e004      	b.n	0x1078cd2a
1078cd20:	2200      	movs	r2, #0
1078cd22:	48fd      	ldr	r0, [pc, #1012]	@ (0x1078d118)
1078cd24:	2300      	movs	r3, #0
1078cd26:	f0b2 ea82 	blx	0x1083f22c
1078cd2a:	2e00      	cmp	r6, #0
1078cd2c:	d007      	beq.n	0x1078cd3e
1078cd2e:	6820      	ldr	r0, [r4, #0]
1078cd30:	f0b2 eace 	blx	0x1083f2d0
1078cd34:	2000      	movs	r0, #0
1078cd36:	6020      	str	r0, [r4, #0]
1078cd38:	b017      	add	sp, #92	@ 0x5c
1078cd3a:	2001      	movs	r0, #1
1078cd3c:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cd3e:	b017      	add	sp, #92	@ 0x5c
1078cd40:	2000      	movs	r0, #0
1078cd42:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cd44:	b500      	push	{lr}
1078cd46:	b083      	sub	sp, #12
1078cd48:	4603      	mov	r3, r0
1078cd4a:	20a5      	movs	r0, #165	@ 0xa5
1078cd4c:	4af3      	ldr	r2, [pc, #972]	@ (0x1078d11c)
1078cd4e:	0100      	lsls	r0, r0, #4
1078cd50:	1819      	adds	r1, r3, r0
1078cd52:	301c      	adds	r0, #28
1078cd54:	1818      	adds	r0, r3, r0
1078cd56:	9202      	str	r2, [sp, #8]
1078cd58:	22ff      	movs	r2, #255	@ 0xff
1078cd5a:	9000      	str	r0, [sp, #0]
1078cd5c:	9101      	str	r1, [sp, #4]
1078cd5e:	2100      	movs	r1, #0
1078cd60:	320b      	adds	r2, #11
1078cd62:	4618      	mov	r0, r3
1078cd64:	2397      	movs	r3, #151	@ 0x97
1078cd66:	f7ff ff53 	bl	0x1078cc10
1078cd6a:	2800      	cmp	r0, #0
1078cd6c:	d002      	beq.n	0x1078cd74
1078cd6e:	b003      	add	sp, #12
1078cd70:	2001      	movs	r0, #1
1078cd72:	bd00      	pop	{pc}
1078cd74:	b003      	add	sp, #12
1078cd76:	2000      	movs	r0, #0
1078cd78:	bd00      	pop	{pc}
1078cd7a:	b5f0      	push	{r4, r5, r6, r7, lr}
1078cd7c:	b083      	sub	sp, #12
1078cd7e:	4606      	mov	r6, r0
1078cd80:	2800      	cmp	r0, #0
1078cd82:	d107      	bne.n	0x1078cd94
1078cd84:	2200      	movs	r2, #0
1078cd86:	2100      	movs	r1, #0
1078cd88:	48e5      	ldr	r0, [pc, #916]	@ (0x1078d120)
1078cd8a:	2300      	movs	r3, #0
1078cd8c:	f0b2 ea4e 	blx	0x1083f22c
1078cd90:	b003      	add	sp, #12
1078cd92:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cd94:	4634      	mov	r4, r6
1078cd96:	34ff      	adds	r4, #255	@ 0xff
1078cd98:	34c1      	adds	r4, #193	@ 0xc1
1078cd9a:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078cd9c:	2800      	cmp	r0, #0
1078cd9e:	d107      	bne.n	0x1078cdb0
1078cda0:	2200      	movs	r2, #0
1078cda2:	2100      	movs	r1, #0
1078cda4:	48df      	ldr	r0, [pc, #892]	@ (0x1078d124)
1078cda6:	2300      	movs	r3, #0
1078cda8:	f0b2 ea40 	blx	0x1083f22c
1078cdac:	b003      	add	sp, #12
1078cdae:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cdb0:	6800      	ldr	r0, [r0, #0]
1078cdb2:	2700      	movs	r7, #0
1078cdb4:	2800      	cmp	r0, #0
1078cdb6:	d00d      	beq.n	0x1078cdd4
1078cdb8:	2200      	movs	r2, #0
1078cdba:	2100      	movs	r1, #0
1078cdbc:	48da      	ldr	r0, [pc, #872]	@ (0x1078d128)
1078cdbe:	2300      	movs	r3, #0
1078cdc0:	f0b2 ea34 	blx	0x1083f22c
1078cdc4:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078cdc6:	2800      	cmp	r0, #0
1078cdc8:	d0f0      	beq.n	0x1078cdac
1078cdca:	f0b2 ea82 	blx	0x1083f2d0
1078cdce:	62a7      	str	r7, [r4, #40]	@ 0x28
1078cdd0:	b003      	add	sp, #12
1078cdd2:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cdd4:	2008      	movs	r0, #8
1078cdd6:	f0b2 ea74 	blx	0x1083f2c0
1078cdda:	4605      	mov	r5, r0
1078cddc:	2d00      	cmp	r5, #0
1078cdde:	d10d      	bne.n	0x1078cdfc
1078cde0:	2200      	movs	r2, #0
1078cde2:	2100      	movs	r1, #0
1078cde4:	48d1      	ldr	r0, [pc, #836]	@ (0x1078d12c)
1078cde6:	2300      	movs	r3, #0
1078cde8:	f0b2 ea20 	blx	0x1083f22c
1078cdec:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078cdee:	2800      	cmp	r0, #0
1078cdf0:	d0ee      	beq.n	0x1078cdd0
1078cdf2:	f0b2 ea6e 	blx	0x1083f2d0
1078cdf6:	62a7      	str	r7, [r4, #40]	@ 0x28
1078cdf8:	b003      	add	sp, #12
1078cdfa:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cdfc:	2004      	movs	r0, #4
1078cdfe:	f0b2 ea60 	blx	0x1083f2c0
1078ce02:	6028      	str	r0, [r5, #0]
1078ce04:	606f      	str	r7, [r5, #4]
1078ce06:	2800      	cmp	r0, #0
1078ce08:	d110      	bne.n	0x1078ce2c
1078ce0a:	2200      	movs	r2, #0
1078ce0c:	2100      	movs	r1, #0
1078ce0e:	48c8      	ldr	r0, [pc, #800]	@ (0x1078d130)
1078ce10:	2300      	movs	r3, #0
1078ce12:	f0b2 ea0c 	blx	0x1083f22c
1078ce16:	4628      	mov	r0, r5
1078ce18:	f0b2 ea5a 	blx	0x1083f2d0
1078ce1c:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078ce1e:	2800      	cmp	r0, #0
1078ce20:	d0ea      	beq.n	0x1078cdf8
1078ce22:	f0b2 ea56 	blx	0x1083f2d0
1078ce26:	62a7      	str	r7, [r4, #40]	@ 0x28
1078ce28:	b003      	add	sp, #12
1078ce2a:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078ce2c:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078ce2e:	68c1      	ldr	r1, [r0, #12]
1078ce30:	6b30      	ldr	r0, [r6, #48]	@ 0x30
1078ce32:	6802      	ldr	r2, [r0, #0]
1078ce34:	3280      	adds	r2, #128	@ 0x80
1078ce36:	6813      	ldr	r3, [r2, #0]
1078ce38:	462a      	mov	r2, r5
1078ce3a:	4798      	blx	r3
1078ce3c:	2800      	cmp	r0, #0
1078ce3e:	d1f3      	bne.n	0x1078ce28
1078ce40:	6828      	ldr	r0, [r5, #0]
1078ce42:	2800      	cmp	r0, #0
1078ce44:	d002      	beq.n	0x1078ce4c
1078ce46:	6800      	ldr	r0, [r0, #0]
1078ce48:	2800      	cmp	r0, #0
1078ce4a:	d117      	bne.n	0x1078ce7c
1078ce4c:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078ce4e:	2200      	movs	r2, #0
1078ce50:	2300      	movs	r3, #0
1078ce52:	8901      	ldrh	r1, [r0, #8]
1078ce54:	48b7      	ldr	r0, [pc, #732]	@ (0x1078d134)
1078ce56:	f0b2 e9ea 	blx	0x1083f22c
1078ce5a:	6828      	ldr	r0, [r5, #0]
1078ce5c:	2800      	cmp	r0, #0
1078ce5e:	d002      	beq.n	0x1078ce66
1078ce60:	f0b2 ea36 	blx	0x1083f2d0
1078ce64:	602f      	str	r7, [r5, #0]
1078ce66:	4628      	mov	r0, r5
1078ce68:	f0b2 ea32 	blx	0x1083f2d0
1078ce6c:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078ce6e:	2800      	cmp	r0, #0
1078ce70:	d0da      	beq.n	0x1078ce28
1078ce72:	f0b2 ea2e 	blx	0x1083f2d0
1078ce76:	62a7      	str	r7, [r4, #40]	@ 0x28
1078ce78:	b003      	add	sp, #12
1078ce7a:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078ce7c:	f0b2 ea20 	blx	0x1083f2c0
1078ce80:	6068      	str	r0, [r5, #4]
1078ce82:	2800      	cmp	r0, #0
1078ce84:	d11c      	bne.n	0x1078cec0
1078ce86:	2200      	movs	r2, #0
1078ce88:	2100      	movs	r1, #0
1078ce8a:	48ab      	ldr	r0, [pc, #684]	@ (0x1078d138)
1078ce8c:	2300      	movs	r3, #0
1078ce8e:	f0b2 e9ce 	blx	0x1083f22c
1078ce92:	6828      	ldr	r0, [r5, #0]
1078ce94:	2800      	cmp	r0, #0
1078ce96:	d002      	beq.n	0x1078ce9e
1078ce98:	f0b2 ea1a 	blx	0x1083f2d0
1078ce9c:	602f      	str	r7, [r5, #0]
1078ce9e:	6868      	ldr	r0, [r5, #4]
1078cea0:	2800      	cmp	r0, #0
1078cea2:	d002      	beq.n	0x1078ceaa
1078cea4:	f0b2 ea14 	blx	0x1083f2d0
1078cea8:	606f      	str	r7, [r5, #4]
1078ceaa:	4628      	mov	r0, r5
1078ceac:	f0b2 ea10 	blx	0x1083f2d0
1078ceb0:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078ceb2:	2800      	cmp	r0, #0
1078ceb4:	d0e0      	beq.n	0x1078ce78
1078ceb6:	f0b2 ea0c 	blx	0x1083f2d0
1078ceba:	62a7      	str	r7, [r4, #40]	@ 0x28
1078cebc:	b003      	add	sp, #12
1078cebe:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cec0:	6aa1      	ldr	r1, [r4, #40]	@ 0x28
1078cec2:	8908      	ldrh	r0, [r1, #8]
1078cec4:	28a9      	cmp	r0, #169	@ 0xa9
1078cec6:	d002      	beq.n	0x1078cece
1078cec8:	38ff      	subs	r0, #255	@ 0xff
1078ceca:	3824      	subs	r0, #36	@ 0x24
1078cecc:	d129      	bne.n	0x1078cf22
1078cece:	6b30      	ldr	r0, [r6, #48]	@ 0x30
1078ced0:	68c9      	ldr	r1, [r1, #12]
1078ced2:	6802      	ldr	r2, [r0, #0]
1078ced4:	3280      	adds	r2, #128	@ 0x80
1078ced6:	6813      	ldr	r3, [r2, #0]
1078ced8:	462a      	mov	r2, r5
1078ceda:	4798      	blx	r3
1078cedc:	2800      	cmp	r0, #0
1078cede:	d10b      	bne.n	0x1078cef8
1078cee0:	4996      	ldr	r1, [pc, #600]	@ (0x1078d13c)
1078cee2:	9501      	str	r5, [sp, #4]
1078cee4:	2307      	movs	r3, #7
1078cee6:	9100      	str	r1, [sp, #0]
1078cee8:	68f0      	ldr	r0, [r6, #12]
1078ceea:	4a95      	ldr	r2, [pc, #596]	@ (0x1078d140)
1078ceec:	6801      	ldr	r1, [r0, #0]
1078ceee:	6d4d      	ldr	r5, [r1, #84]	@ 0x54
1078cef0:	2102      	movs	r1, #2
1078cef2:	031b      	lsls	r3, r3, #12
1078cef4:	47a8      	blx	r5
1078cef6:	e014      	b.n	0x1078cf22
1078cef8:	2200      	movs	r2, #0
1078cefa:	2100      	movs	r1, #0
1078cefc:	4891      	ldr	r0, [pc, #580]	@ (0x1078d144)
1078cefe:	2300      	movs	r3, #0
1078cf00:	f0b2 e994 	blx	0x1083f22c
1078cf04:	6828      	ldr	r0, [r5, #0]
1078cf06:	2800      	cmp	r0, #0
1078cf08:	d002      	beq.n	0x1078cf10
1078cf0a:	f0b2 e9e2 	blx	0x1083f2d0
1078cf0e:	602f      	str	r7, [r5, #0]
1078cf10:	6868      	ldr	r0, [r5, #4]
1078cf12:	2800      	cmp	r0, #0
1078cf14:	d002      	beq.n	0x1078cf1c
1078cf16:	f0b2 e9dc 	blx	0x1083f2d0
1078cf1a:	606f      	str	r7, [r5, #4]
1078cf1c:	4628      	mov	r0, r5
1078cf1e:	f0b2 e9d8 	blx	0x1083f2d0
1078cf22:	6aa0      	ldr	r0, [r4, #40]	@ 0x28
1078cf24:	2800      	cmp	r0, #0
1078cf26:	d0c9      	beq.n	0x1078cebc
1078cf28:	f0b2 e9d2 	blx	0x1083f2d0
1078cf2c:	62a7      	str	r7, [r4, #40]	@ 0x28
1078cf2e:	b003      	add	sp, #12
1078cf30:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cf32:	b500      	push	{lr}
1078cf34:	b083      	sub	sp, #12
1078cf36:	4603      	mov	r3, r0
1078cf38:	4619      	mov	r1, r3
1078cf3a:	31ff      	adds	r1, #255	@ 0xff
1078cf3c:	31cd      	adds	r1, #205	@ 0xcd
1078cf3e:	4a82      	ldr	r2, [pc, #520]	@ (0x1078d148)
1078cf40:	4608      	mov	r0, r1
1078cf42:	301c      	adds	r0, #28
1078cf44:	9202      	str	r2, [sp, #8]
1078cf46:	22ff      	movs	r2, #255	@ 0xff
1078cf48:	9000      	str	r0, [sp, #0]
1078cf4a:	9101      	str	r1, [sp, #4]
1078cf4c:	2100      	movs	r1, #0
1078cf4e:	3224      	adds	r2, #36	@ 0x24
1078cf50:	4618      	mov	r0, r3
1078cf52:	23a9      	movs	r3, #169	@ 0xa9
1078cf54:	f7ff fe5c 	bl	0x1078cc10
1078cf58:	2800      	cmp	r0, #0
1078cf5a:	d002      	beq.n	0x1078cf62
1078cf5c:	b003      	add	sp, #12
1078cf5e:	2001      	movs	r0, #1
1078cf60:	bd00      	pop	{pc}
1078cf62:	b003      	add	sp, #12
1078cf64:	2000      	movs	r0, #0
1078cf66:	bd00      	pop	{pc}
1078cf68:	b5f0      	push	{r4, r5, r6, r7, lr}
1078cf6a:	b083      	sub	sp, #12
1078cf6c:	4606      	mov	r6, r0
1078cf6e:	2700      	movs	r7, #0
1078cf70:	2800      	cmp	r0, #0
1078cf72:	d107      	bne.n	0x1078cf84
1078cf74:	2200      	movs	r2, #0
1078cf76:	2100      	movs	r1, #0
1078cf78:	4874      	ldr	r0, [pc, #464]	@ (0x1078d14c)
1078cf7a:	2300      	movs	r3, #0
1078cf7c:	f0b2 e956 	blx	0x1083f22c
1078cf80:	b003      	add	sp, #12
1078cf82:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cf84:	4634      	mov	r4, r6
1078cf86:	34ff      	adds	r4, #255	@ 0xff
1078cf88:	3441      	adds	r4, #65	@ 0x41
1078cf8a:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078cf8c:	2800      	cmp	r0, #0
1078cf8e:	d10e      	bne.n	0x1078cfae
1078cf90:	2200      	movs	r2, #0
1078cf92:	2100      	movs	r1, #0
1078cf94:	486e      	ldr	r0, [pc, #440]	@ (0x1078d150)
1078cf96:	2300      	movs	r3, #0
1078cf98:	f0b2 e948 	blx	0x1083f22c
1078cf9c:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078cf9e:	2800      	cmp	r0, #0
1078cfa0:	d0ee      	beq.n	0x1078cf80
1078cfa2:	f0b2 e996 	blx	0x1083f2d0
1078cfa6:	2000      	movs	r0, #0
1078cfa8:	6320      	str	r0, [r4, #48]	@ 0x30
1078cfaa:	b003      	add	sp, #12
1078cfac:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cfae:	6800      	ldr	r0, [r0, #0]
1078cfb0:	2800      	cmp	r0, #0
1078cfb2:	d00e      	beq.n	0x1078cfd2
1078cfb4:	2200      	movs	r2, #0
1078cfb6:	2100      	movs	r1, #0
1078cfb8:	4866      	ldr	r0, [pc, #408]	@ (0x1078d154)
1078cfba:	2300      	movs	r3, #0
1078cfbc:	f0b2 e936 	blx	0x1083f22c
1078cfc0:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078cfc2:	2800      	cmp	r0, #0
1078cfc4:	d0f1      	beq.n	0x1078cfaa
1078cfc6:	f0b2 e984 	blx	0x1083f2d0
1078cfca:	2000      	movs	r0, #0
1078cfcc:	6320      	str	r0, [r4, #48]	@ 0x30
1078cfce:	b003      	add	sp, #12
1078cfd0:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cfd2:	2008      	movs	r0, #8
1078cfd4:	f0b2 e974 	blx	0x1083f2c0
1078cfd8:	4605      	mov	r5, r0
1078cfda:	2d00      	cmp	r5, #0
1078cfdc:	d10e      	bne.n	0x1078cffc
1078cfde:	2200      	movs	r2, #0
1078cfe0:	2100      	movs	r1, #0
1078cfe2:	485d      	ldr	r0, [pc, #372]	@ (0x1078d158)
1078cfe4:	2300      	movs	r3, #0
1078cfe6:	f0b2 e922 	blx	0x1083f22c
1078cfea:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078cfec:	2800      	cmp	r0, #0
1078cfee:	d0ee      	beq.n	0x1078cfce
1078cff0:	f0b2 e96e 	blx	0x1083f2d0
1078cff4:	2000      	movs	r0, #0
1078cff6:	6320      	str	r0, [r4, #48]	@ 0x30
1078cff8:	b003      	add	sp, #12
1078cffa:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078cffc:	2004      	movs	r0, #4
1078cffe:	f0b2 e960 	blx	0x1083f2c0
1078d002:	6028      	str	r0, [r5, #0]
1078d004:	2100      	movs	r1, #0
1078d006:	6069      	str	r1, [r5, #4]
1078d008:	2800      	cmp	r0, #0
1078d00a:	d110      	bne.n	0x1078d02e
1078d00c:	2200      	movs	r2, #0
1078d00e:	4853      	ldr	r0, [pc, #332]	@ (0x1078d15c)
1078d010:	2300      	movs	r3, #0
1078d012:	f0b2 e90c 	blx	0x1083f22c
1078d016:	4628      	mov	r0, r5
1078d018:	f0b2 e95a 	blx	0x1083f2d0
1078d01c:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d01e:	2800      	cmp	r0, #0
1078d020:	d0ea      	beq.n	0x1078cff8
1078d022:	f0b2 e956 	blx	0x1083f2d0
1078d026:	2100      	movs	r1, #0
1078d028:	6321      	str	r1, [r4, #48]	@ 0x30
1078d02a:	b003      	add	sp, #12
1078d02c:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078d02e:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d030:	68c1      	ldr	r1, [r0, #12]
1078d032:	6b30      	ldr	r0, [r6, #48]	@ 0x30
1078d034:	6802      	ldr	r2, [r0, #0]
1078d036:	3280      	adds	r2, #128	@ 0x80
1078d038:	6813      	ldr	r3, [r2, #0]
1078d03a:	462a      	mov	r2, r5
1078d03c:	4798      	blx	r3
1078d03e:	2800      	cmp	r0, #0
1078d040:	d1f3      	bne.n	0x1078d02a
1078d042:	6828      	ldr	r0, [r5, #0]
1078d044:	2800      	cmp	r0, #0
1078d046:	d002      	beq.n	0x1078d04e
1078d048:	6800      	ldr	r0, [r0, #0]
1078d04a:	2800      	cmp	r0, #0
1078d04c:	d119      	bne.n	0x1078d082
1078d04e:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d050:	2200      	movs	r2, #0
1078d052:	2300      	movs	r3, #0
1078d054:	8901      	ldrh	r1, [r0, #8]
1078d056:	4842      	ldr	r0, [pc, #264]	@ (0x1078d160)
1078d058:	f0b2 e8e8 	blx	0x1083f22c
1078d05c:	6828      	ldr	r0, [r5, #0]
1078d05e:	2800      	cmp	r0, #0
1078d060:	d003      	beq.n	0x1078d06a
1078d062:	f0b2 e936 	blx	0x1083f2d0
1078d066:	2100      	movs	r1, #0
1078d068:	6029      	str	r1, [r5, #0]
1078d06a:	4628      	mov	r0, r5
1078d06c:	f0b2 e930 	blx	0x1083f2d0
1078d070:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d072:	2800      	cmp	r0, #0
1078d074:	d0d9      	beq.n	0x1078d02a
1078d076:	f0b2 e92c 	blx	0x1083f2d0
1078d07a:	2100      	movs	r1, #0
1078d07c:	6321      	str	r1, [r4, #48]	@ 0x30
1078d07e:	b003      	add	sp, #12
1078d080:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078d082:	f0b2 e91e 	blx	0x1083f2c0
1078d086:	6068      	str	r0, [r5, #4]
1078d088:	2800      	cmp	r0, #0
1078d08a:	d11f      	bne.n	0x1078d0cc
1078d08c:	2200      	movs	r2, #0
1078d08e:	2100      	movs	r1, #0
1078d090:	4834      	ldr	r0, [pc, #208]	@ (0x1078d164)
1078d092:	2300      	movs	r3, #0
1078d094:	f0b2 e8ca 	blx	0x1083f22c
1078d098:	6828      	ldr	r0, [r5, #0]
1078d09a:	2800      	cmp	r0, #0
1078d09c:	d003      	beq.n	0x1078d0a6
1078d09e:	f0b2 e918 	blx	0x1083f2d0
1078d0a2:	2100      	movs	r1, #0
1078d0a4:	6029      	str	r1, [r5, #0]
1078d0a6:	6868      	ldr	r0, [r5, #4]
1078d0a8:	2800      	cmp	r0, #0
1078d0aa:	d003      	beq.n	0x1078d0b4
1078d0ac:	f0b2 e910 	blx	0x1083f2d0
1078d0b0:	2100      	movs	r1, #0
1078d0b2:	6069      	str	r1, [r5, #4]
1078d0b4:	4628      	mov	r0, r5
1078d0b6:	f0b2 e90c 	blx	0x1083f2d0
1078d0ba:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d0bc:	2800      	cmp	r0, #0
1078d0be:	d0de      	beq.n	0x1078d07e
1078d0c0:	f0b2 e906 	blx	0x1083f2d0
1078d0c4:	2100      	movs	r1, #0
1078d0c6:	6321      	str	r1, [r4, #48]	@ 0x30
1078d0c8:	b003      	add	sp, #12
1078d0ca:	bdf0      	pop	{r4, r5, r6, r7, pc}
1078d0cc:	6b20      	ldr	r0, [r4, #48]	@ 0x30
1078d0ce:	68c1      	ldr	r1, [r0, #12]
