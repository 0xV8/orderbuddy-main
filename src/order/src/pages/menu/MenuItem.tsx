import { IonCard, IonCardHeader, IonCardSubtitle, IonCardTitle, IonText } from '@ionic/react';
import React from 'react';
import { getUserLang, t } from '@/utils/localization';
import { MenuItemType } from './components/types/menu';

export interface MenuItemProps {
  item: MenuItemType;
  onClick?: (item: MenuItemType) => void;
}

const MenuItem: React.FC<MenuItemProps> = ({ item, onClick }) => {
  const currentLang = getUserLang();
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  return (
    <div>
      <IonCard onClick={handleClick}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '200px',
            overflow: 'hidden',
          }}
        >
          <img
            alt={t(item.name, currentLang)}
            src={
              item?.imageUrls && item.imageUrls[0]
                ? item.imageUrls[0]
                : 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=400&fit=crop'
            }
            style={{ objectFit: 'cover', width: '100%', height: '100%' }}
            onError={(e) => {
              e.currentTarget.src = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=400&fit=crop';
            }}
          />
        </div>
        <IonCardHeader>
          <IonCardTitle>
            <IonText className='font-size-14'> {t(item.name, currentLang)}</IonText>
          </IonCardTitle>
          <IonCardSubtitle className='font-size-14'>${(item?.priceCents / 100).toFixed(2)}</IonCardSubtitle>
        </IonCardHeader>
      </IonCard>
    </div>
  );
};

export default MenuItem;
