chunk_sizes = [25, 50, 75, 100, 200]

seq = 6.9105;

t_4 = [12.5365428925,12.5494630337,12.8019931316,12.3967452049,13.4420061111];
t_2 = [14.8120741844,14.9045131207,14.9622340202,15.5535850525,15.4479911327];


io_2 = [9.69118952751,9.95887303352,9.84942698479,11.0126080513,9.98553681374];
io_4 = [11.7974779606,11.0756087303,11.5668187141,11.2734808922,12.0836229324];

ct_2 = t_2 - io_2;
ct_4 = t_4 - io_4;

figure(1);
plot([chunk_sizes(1), chunk_sizes(5)], [seq, seq], chunk_sizes, t_4, chunk_sizes, t_2, chunk_sizes, io_4, chunk_sizes, io_2,
     chunk_sizes, ct_4, chunk_sizes, ct_2);
ylabel('Time (s)');
xlabel("Chunks' Size (x1000)");
axis([25, 200])
legend('Sequential', '4 threads', '2 threads', 'IO 4 threads', 'IO 2 threads', 'Time w/o IO 4 threads', 'Time w/o IO 2 threads');

set(gca,'XTick', 25:25:200)

print('./img/medium_graph.png','-color','-dpng','-r600');
