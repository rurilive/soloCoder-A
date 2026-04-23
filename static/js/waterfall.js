document.addEventListener('DOMContentLoaded', function() {
    const waterfall = document.getElementById('waterfall');
    
    if (waterfall) {
        const items = waterfall.querySelectorAll('.waterfall-item');
        
        const observer = new IntersectionObserver(
            function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '50px'
            }
        );
        
        items.forEach(function(item, index) {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            item.style.transitionDelay = (index * 0.05) + 's';
            observer.observe(item);
        });
    }
});
