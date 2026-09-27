// Decompiled 61u.key validation cluster, APPS.bin 1.1.2 (Ghidra 12.1, ARM LE v8).
// See re/notes.md section 2b-2d. Generated 2026-09-27.

// ===== FUN_108d0a96 (from /tmp/dec_0a96.log) =====
undefined4
FUN_108d0a96(int param_1,undefined4 *param_2,char *param_3,char *param_4,undefined2 *param_5,
            undefined2 param_6,undefined2 param_7)

{
  int iVar1;
  
  if (param_1 == 0) {
    return 1;
  }
  iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x2c))(*(int **)(param_1 + 0x30),param_3);
  if (iVar1 != 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bf4,0,0,0);
  }
  if ((*param_3 == '\0') && (param_3[2] == '\0')) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0c00,0,0,0);
  }
  iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x44))(*(int **)(param_1 + 0x30),1,param_4);
  if (iVar1 != 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bf8,0,0,0);
  }
  if ((*param_4 == '\0') &&
     (iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x44))(*(int **)(param_1 + 0x30),3,param_4),
     iVar1 != 0)) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bfc,0,0,0);
  }
  if (*param_4 == '\x01') {
    if ((int)((uint)(byte)param_3[1] << 0x1d) < 0) {
      *(undefined2 *)((int)param_2 + 6) = param_6;
      *param_5 = param_6;
    }
    else {
      if (-1 < (int)((uint)(byte)param_3[1] << 0x1e)) {
                    /* WARNING: Subroutine does not return */
        thunk_FUN_1014e902(DAT_108d0c04,0,0,0);
      }
      *(undefined2 *)((int)param_2 + 6) = param_7;
      *param_5 = param_7;
    }
  }
  else {
    if (*param_4 != '\x02') {
                    /* WARNING: Subroutine does not return */
      thunk_FUN_1014e902(DAT_108d0c0c,0,0,0);
    }
    if ((int)((uint)(byte)param_3[3] << 0x1d) < 0) {
      *(undefined2 *)((int)param_2 + 6) = param_6;
      *param_5 = param_6;
    }
    else {
      if (-1 < (int)((uint)(byte)param_3[3] << 0x1e)) {
                    /* WARNING: Subroutine does not return */
        thunk_FUN_1014e902(DAT_108d0c08,0,0,0);
      }
      *(undefined2 *)((int)param_2 + 6) = param_7;
      *param_5 = param_7;
    }
  }
  param_2[2] = 0;
  param_2[3] = 0;
  param_2[4] = 0;
  param_2[5] = 0;
  *(undefined2 *)(param_2 + 1) = 1;
  *param_2 = 0x18;
  return 0;
}

// ===== FUN_108d0c10 (from /tmp/dec_0c10.log) =====
undefined4
FUN_108d0c10(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,int *param_5,
            int param_6,undefined4 param_7)

{
  int iVar1;
  uint uVar2;
  ushort local_4c [2];
  undefined1 local_48 [4];
  undefined1 auStack_44 [8];
  undefined4 local_3c;
  undefined4 local_38;
  undefined4 local_34;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  undefined4 uStack_28;
  int iStack_24;
  undefined4 local_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  
  iStack_24 = param_1;
  local_20 = param_2;
  uStack_1c = param_3;
  uStack_18 = param_4;
  iVar1 = FUN_108d0a96(param_1,&local_3c,auStack_44,local_48,local_4c,param_3,param_4);
  if (iVar1 != 0) {
    return 1;
  }
  iVar1 = thunk_FUN_10d6f944(0x10);
  *param_5 = iVar1;
  if (iVar1 == 0) {
    return 1;
  }
  *(undefined4 *)(param_6 + 0x10) = param_7;
  *(int *)(param_6 + 0x14) = param_1;
  uVar2 = (uint)local_4c[0];
  iVar1 = uVar2 - 0x10a;
  if (uVar2 != 0x10a) {
    if (0x10a < uVar2) {
      if (iVar1 == 0x5c) {
LAB_108d0c9c:
        iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x6c))
                          (*(int **)(param_1 + 0x30),local_48[0],local_3c,local_38,local_34,
                           uStack_30,uStack_2c,uStack_28,*(ushort *)(param_1 + 0x1ee) + 1,*param_5,
                           param_6);
      }
      else {
        if (iVar1 < 0x5d) {
          if (iVar1 == 0x19) goto LAB_108d0cf6;
          if (iVar1 != 0x5b) goto LAB_108d0d20;
        }
        else if (iVar1 != 0x5d) {
          if (iVar1 != 0x5e) goto LAB_108d0d20;
          goto LAB_108d0c9c;
        }
        iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x6c))
                          (*(int **)(param_1 + 0x30),local_48[0],local_3c,local_38,local_34,
                           uStack_30,uStack_2c,uStack_28,*(ushort *)(param_1 + 0x458) + 1,*param_5,
                           param_6);
      }
      goto LAB_108d0d2a;
    }
    if (uVar2 != 0xa9) {
      if (uVar2 < 0xaa) {
        if ((uVar2 != 0x6d) && ((uVar2 != 0x76 && (uVar2 != 0x97)))) {
LAB_108d0d20:
                    /* WARNING: Subroutine does not return */
          thunk_FUN_1014e902(DAT_108d1118,uVar2,0,0);
        }
      }
      else if ((uVar2 != 0xcf) && (uVar2 != 0xda)) goto LAB_108d0d20;
    }
  }
LAB_108d0cf6:
  iVar1 = (**(code **)(**(int **)(param_1 + 0x30) + 0x70))
                    (*(int **)(param_1 + 0x30),local_48[0],local_3c,local_38,local_34,uStack_30,
                     uStack_2c,uStack_28,0,local_20,*param_5,param_6);
LAB_108d0d2a:
  if (iVar1 == 0) {
    return 0;
  }
  thunk_FUN_11155878(*param_5);
  *param_5 = 0;
  return 1;
}

// ===== FUN_108d0d44 (from /tmp/dec_0d44.log) =====
undefined4 FUN_108d0d44(int param_1)

{
  int iVar1;
  
  iVar1 = FUN_108d0c10(param_1,0,0x10a,0x97,param_1 + 0xa6c,param_1 + 0xa50,DAT_108d111c);
  if (iVar1 != 0) {
    return 1;
  }
  return 0;
}

// ===== FUN_108d08d0 (from /tmp/dec_raw.log) =====
void FUN_108d08d0(int param_1)

{
  short sVar1;
  int *piVar2;
  int iVar3;
  
  if (param_1 == 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bc8,0,0,0);
  }
  if (*(int **)(param_1 + 0xa6c) == (int *)0x0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bcc,0,0,0);
  }
  if (**(int **)(param_1 + 0xa6c) != 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bd0,0,0,0);
  }
  piVar2 = (int *)thunk_FUN_10d6f944(8);
  if (piVar2 == (int *)0x0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bd4,0,0,0);
  }
  iVar3 = thunk_FUN_10d6f944(4);
  *piVar2 = iVar3;
  piVar2[1] = 0;
  if (iVar3 == 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bd8,0,0,0);
  }
  iVar3 = (**(code **)(**(int **)(param_1 + 0x30) + 0x80))
                    (*(int **)(param_1 + 0x30),*(undefined4 *)(*(int *)(param_1 + 0xa6c) + 0xc),
                     piVar2);
  if (iVar3 != 0) {
    return;
  }
  if (((int *)*piVar2 == (int *)0x0) || (*(int *)*piVar2 == 0)) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bdc,*(undefined2 *)(*(int *)(param_1 + 0xa6c) + 8),0,0);
  }
  iVar3 = thunk_FUN_10d6f944();
  piVar2[1] = iVar3;
  if (iVar3 == 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0be0,0,0,0);
  }
  sVar1 = *(short *)(*(int *)(param_1 + 0xa6c) + 8);
  if ((sVar1 != 0x97) && (sVar1 != 0x10a)) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bf0,0,0,0);
  }
  iVar3 = (**(code **)(**(int **)(param_1 + 0x30) + 0x80))
                    (*(int **)(param_1 + 0x30),*(undefined4 *)(*(int *)(param_1 + 0xa6c) + 0xc),
                     piVar2);
  if (iVar3 != 0) {
                    /* WARNING: Subroutine does not return */
    thunk_FUN_1014e902(DAT_108d0bec,0,0,0);
  }
  (**(code **)(**(int **)(param_1 + 0xc) + 0x54))
            (*(int **)(param_1 + 0xc),2,DAT_108d0be8,0x7000,DAT_108d0be4,piVar2);
  if (*(int *)(param_1 + 0xa6c) != 0) {
    thunk_FUN_11155878();
    *(undefined4 *)(param_1 + 0xa6c) = 0;
    return;
  }
  return;
}

// ===== FUN_1014e744 (from /tmp/dec_e744.log) =====
void FUN_1014e744(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                 undefined4 param_5)

{
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  
  local_14 = param_2;
  local_10 = param_3;
  local_c = param_4;
  FUN_1014e5f2(param_1,&local_14,param_5);
  return;
}

// ===== FUN_1014e902 (from /tmp/dec_1014e902.log) =====
void FUN_1014e902(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  
  iVar2 = param_1;
  uVar3 = param_3;
  uVar4 = param_4;
  iVar1 = FUN_1014e89c(param_1,3);
  if (iVar1 != 0) {
    *(undefined4 *)(iVar1 + 0x10) = param_2;
    *(undefined4 *)(iVar1 + 0x14) = param_3;
    *(undefined4 *)(iVar1 + 0x18) = param_4;
    thunk_FUN_106fe37e(iVar1);
  }
  if ((*(char *)(param_1 + 0x10) != '\0') &&
     (((uint)(*DAT_1014ec1c >> 3) & *(uint *)(param_1 + 4)) != 0)) {
    FUN_1014e744(param_1,param_2,param_3,param_4,iVar1,iVar2,param_2,uVar3,uVar4);
  }
  return;
}
// ===== FUN_108d06ee (file-open helper) =====
int FUN_108d06ee(undefined4 param_1)

{
  undefined4 uVar1;
  int *piVar2;
  int iVar3;
  int *piVar4;
  undefined1 auStack_60 [8];
  int local_58;
  int *local_14;
  
  local_14 = (int *)0x0;
  piVar4 = (int *)0x0;
  thunk_FUN_105c2534(auStack_60,0x4c);
  uVar1 = thunk_FUN_10d469aa();
  piVar2 = (int *)thunk_FUN_10d469aa();
  iVar3 = (**(code **)(*piVar2 + 8))(uVar1,DAT_108d089c,&local_14);
  if ((iVar3 == 0) &&
     (piVar4 = (int *)(**(code **)(*local_14 + 8))(local_14,param_1,1), piVar4 != (int *)0x0)) {
    (**(code **)(*piVar4 + 0x1c))(piVar4,0,0);
    (**(code **)(*local_14 + 0xc))(local_14,param_1,auStack_60);
    iVar3 = thunk_FUN_10d6f944(local_58 + 1);
    if (iVar3 != 0) {
      FUN_107c5c54(iVar3,0,local_58 + 1);
      (**(code **)(*piVar4 + 0xc))(piVar4,iVar3,local_58);
      (**(code **)(*piVar4 + 4))(piVar4);
      (**(code **)(*local_14 + 4))();
      return iVar3;
    }
  }
  if (piVar4 != (int *)0x0) {
    (**(code **)(*piVar4 + 4))(piVar4);
  }
  if (local_14 != (int *)0x0) {
    (**(code **)(*local_14 + 4))();
  }
  return 0;
}
