program main
   use mpi

   integer :: id, n, ierr
   
   call mpi_init(ierr)
   call mpi_comm_rank(mpi_comm_world, id, ierr)
   call mpi_comm_size(mpi_comm_world, n, ierr)

   write (0,*) "Task ",id, "of ",n

   call mpi_finalize(ierr)

end program main
