
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_eaf7d270cb319ced178804fa4a50898a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_12ec703b4078a42db5cdee326834ddda = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_create_cat", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 10px", ["borderRadius"] : "8px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["background"] : "rgba(255,255,255,0.08)", ["cursor"] : "pointer", ["flexShrink"] : "0", ["&:hover"] : ({ ["borderColor"] : "rgba(255,255,255,0.14)" }) }),onClick:on_click_12ec703b4078a42db5cdee326834ddda},children)
    )
});
